// The camera: it always looks from the same corner (isometric view) and only moves and zooms.
// Overview: the whole pipeline. A chosen step: close to that object, gliding there in 0.8 s
// (with "reduce motion" it jumps). It also keeps the names of the steps in the right place.
import { useContext, useLayoutEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Vector3 } from "three";
import { MotionContext } from "./motion.js";

const OFFSET = new Vector3(20, 20, 20); // where the camera stands, seen from what it looks at
const RIGHT = new Vector3(1, 0, -1).normalize(); // "right" on the screen, in scene directions

const OVERVIEW = { target: new Vector3(0, 0.1, 0), width: 21.8, height: 7.6 };
const CLOSE = { width: 6.4, height: 4.6, lift: 0.7 };
const SECONDS = 0.8;

// Fast start, soft end: close to cubic-bezier(0.16, 1, 0.3, 1) of kinetics.colorion.co
const ease = (x) => 1 - (1 - x) ** 5;

/**
 * Where the camera should look and how much it zooms.
 * `side`: pixels covered by the panel on the right; the object sits in the middle of the rest.
 */
function goalFor({ selected, side }, size, positions) {
  const free = Math.max(size.width - side, 1);
  let target;
  let zoom;
  if (selected == null) {
    target = OVERVIEW.target.clone();
    zoom = Math.min(free / OVERVIEW.width, size.height / OVERVIEW.height);
  } else {
    const [x, , z] = positions[selected];
    target = new Vector3(x, CLOSE.lift, z);
    zoom = Math.min(free / CLOSE.width, size.height / CLOSE.height);
  }
  target.addScaledVector(RIGHT, side / 2 / zoom);
  return { target, zoom };
}

export default function CameraRig({ selected, side, positions, labelPoints, labels }) {
  const camera = useThree((state) => state.camera);
  const size = useThree((state) => state.size);
  const invalidate = useThree((state) => state.invalidate);
  const { still } = useContext(MotionContext);
  const view = useRef(null);
  const tween = useRef(null);
  const wanted = useRef({ selected, side });
  wanted.current = { selected, side };

  function apply(next) {
    camera.position.copy(next.target).add(OFFSET);
    camera.lookAt(next.target);
    camera.zoom = next.zoom;
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    view.current = next;
    // The names follow their objects. A name outside the free part of the scene fades out
    // (opacity, not "visibility: hidden": that would take the keyboard focus away),
    // except the one with the focus.
    const free = size.width - wanted.current.side;
    labelPoints.forEach((point, i) => {
      const element = labels.current[i];
      if (!element) return;
      const p = point.clone().project(camera);
      const left = ((p.x + 1) / 2) * size.width;
      const top = ((1 - p.y) / 2) * size.height;
      const inside = left > 30 && left < free - 30 && top > 10 && top < size.height - 10;
      const shown = inside || document.activeElement === element;
      element.style.left = `${left}px`;
      element.style.top = `${top}px`;
      element.style.opacity = shown ? "1" : "0";
      element.style.pointerEvents = shown ? "" : "none";
    });
  }

  // A new size of the scene: jump to the right view, no animation.
  useLayoutEffect(() => {
    tween.current = null;
    apply(goalFor(wanted.current, size, positions));
    invalidate();
  }, [size.width, size.height]); // eslint-disable-line react-hooks/exhaustive-deps

  // A new choice: glide (or jump, with "reduce motion").
  useLayoutEffect(() => {
    const goal = goalFor({ selected, side }, size, positions);
    if (still || !view.current) {
      tween.current = null;
      apply(goal);
    } else {
      tween.current = { from: view.current, to: goal, t: 0 };
    }
    invalidate();
  }, [selected, side]); // eslint-disable-line react-hooks/exhaustive-deps

  useFrame((_, delta) => {
    const glide = tween.current;
    if (!glide) return;
    glide.t = Math.min(glide.t + Math.min(delta, 1 / 30) / SECONDS, 1);
    const k = ease(glide.t);
    apply({
      target: glide.from.target.clone().lerp(glide.to.target, k),
      zoom: glide.from.zoom + (glide.to.zoom - glide.from.zoom) * k,
    });
    if (glide.t >= 1) tween.current = null;
    else invalidate();
  });

  return null;
}
