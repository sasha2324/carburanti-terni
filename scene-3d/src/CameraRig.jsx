// The camera: it always looks from the same corner (isometric view) and only moves and zooms.
// Overview: the whole pipeline. A chosen step: close to that object, gliding there in 0.8 s
// (with "reduce motion" it jumps). It also keeps the names of the steps in the right place.
import { useContext, useLayoutEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Vector3 } from "three";
import { MotionContext } from "./motion.js";

const OFFSET = new Vector3(20, 20, 20); // where the camera stands, seen from what it looks at
const RIGHT = new Vector3(1, 0, -1).normalize(); // "right" on the screen, in scene directions
const UP = new Vector3(-1, 2, -1).normalize(); // "up" on the screen, in scene directions

// What each layout shows, in scene units: the whole scene (overview) or one step (close).
const VIEWS = {
  row: {
    overview: { target: new Vector3(0, 0.1, 0), width: 21.8, height: 7.6 },
    close: { width: 6.4, height: 4.6, shift: 0 },
  },
  column: {
    // the names stand on the right of the steps: the centre of the picture moves right
    overview: { target: new Vector3().addScaledVector(RIGHT, 0.75).addScaledVector(UP, 0.6), width: 7.0, height: 14.2 },
    // close: the step a bit to the left, so its name (on the right) fits too
    close: { width: 5.4, height: 5.6, shift: 0.9 },
  },
};
const LIFT = 0.7; // close to a step, look a bit above the ground
const SECONDS = 0.8;

// Fast start, soft end: close to cubic-bezier(0.16, 1, 0.3, 1) of kinetics.colorion.co
const ease = (x) => 1 - (1 - x) ** 5;

/**
 * Where the camera should look and how much it zooms.
 * `side`: pixels covered by the panel on the right; the object sits in the middle of the rest.
 */
function goalFor({ selected, side, layout }, size) {
  const free = Math.max(size.width - side, 1);
  const { overview, close } = VIEWS[layout.name];
  let target;
  let zoom;
  if (selected == null) {
    target = overview.target.clone();
    zoom = Math.min(free / overview.width, size.height / overview.height);
  } else {
    const [x, , z] = layout.positions[selected];
    target = new Vector3(x, LIFT, z).addScaledVector(RIGHT, close.shift);
    zoom = Math.min(free / close.width, size.height / close.height);
  }
  target.addScaledVector(RIGHT, side / 2 / zoom);
  return { target, zoom };
}

export default function CameraRig({ selected, side, layout, labelPoints, labels }) {
  const camera = useThree((state) => state.camera);
  const size = useThree((state) => state.size);
  const invalidate = useThree((state) => state.invalidate);
  const { still } = useContext(MotionContext);
  const view = useRef(null);
  const tween = useRef(null);
  const wanted = useRef({ selected, side, layout });
  wanted.current = { selected, side, layout };

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

  // A new size or layout of the scene: jump to the right view, no animation.
  useLayoutEffect(() => {
    tween.current = null;
    apply(goalFor(wanted.current, size));
    invalidate();
  }, [size.width, size.height, layout]); // eslint-disable-line react-hooks/exhaustive-deps

  // A new choice: glide (or jump, with "reduce motion").
  useLayoutEffect(() => {
    const goal = goalFor(wanted.current, size);
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
