// The drops of data in the "Download" glass pipes: from the Ministry, through the pump,
// to the filter. About one drop in ten is a wrong price (red): at the filter it slides
// down the chute and falls into the bin. (The real share is much smaller: the panels
// of the next step show the real numbers.)
import { useMemo, useRef } from "react";
import { BIN_BOTTOM, CHUTE, route, turnPoint } from "../layout.js";
import { easeInQuad, useTicker } from "../motion.js";
import { Solid } from "../parts.jsx";

const COUNT = 10;
const WRONG = 3; // the index of the red drop
const SPEED = 1.1; // scene units per second
const INSIDE_PUMP = 1.0; // hidden length inside the pump
const SLIDE = 0.8; // seconds on the chute
const FALL = 0.5; // seconds from the chute into the bin

/** The whole path as straight pieces; `hidden` pieces are inside the pump. */
function buildPath(layout) {
  const [ministry, pump, filter] = layout.positions;
  const first = route(ministry, pump, layout);
  const second = route(pump, filter, layout);
  const pieces = [
    { from: first.start, to: first.elbow },
    { from: first.elbow, to: first.end },
    { from: first.end, to: second.start, hidden: true, length: INSIDE_PUMP },
    { from: second.start, to: second.elbow },
    { from: second.elbow, to: second.end },
  ].map((piece) => ({
    ...piece,
    length: piece.length ?? Math.hypot(piece.to[0] - piece.from[0], piece.to[2] - piece.from[2]),
  }));
  return { pieces, length: pieces.reduce((sum, piece) => sum + piece.length, 0) };
}

const mix = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];

/** Where a drop is after `distance` units along the path, and whether it can be seen. */
function pointAt({ pieces }, distance) {
  let rest = distance;
  for (const piece of pieces) {
    if (rest <= piece.length) return { at: mix(piece.from, piece.to, rest / piece.length), visible: !piece.hidden };
    rest -= piece.length;
  }
  const last = pieces[pieces.length - 1];
  return { at: last.to, visible: false };
}

export default function Flow({ colors, layout }) {
  const path = useMemo(() => buildPath(layout), [layout]);
  // The chute and the bin turn with the filter (at the centre of the scene).
  const chute = useMemo(
    () => ({ from: turnPoint(CHUTE.from, layout.turn), to: turnPoint(CHUTE.to, layout.turn), bin: turnPoint(BIN_BOTTOM, layout.turn) }),
    [layout]
  );
  const drops = useRef([]);
  const falling = useRef();

  useTicker((time) => {
    const spacing = path.length / COUNT;
    drops.current.forEach((mesh, i) => {
      const distance = (time * SPEED + i * spacing) % path.length;
      const { at, visible } = pointAt(path, distance);
      mesh.position.set(...at);
      mesh.visible = visible;
      if (i === WRONG) {
        // After the red drop reaches the filter (distance back to 0), a copy goes to the bin.
        const since = distance / SPEED;
        const slide = since / SLIDE;
        const fall = (since - SLIDE) / FALL;
        falling.current.visible = since < SLIDE + FALL;
        if (slide < 1) falling.current.position.set(...mix(chute.from, chute.to, easeInQuad(slide)));
        else falling.current.position.set(...mix(chute.to, chute.bin, easeInQuad(fall)));
      }
    });
  });

  return (
    <group>
      {Array.from({ length: COUNT }, (_, i) => (
        <mesh key={i} ref={(mesh) => (drops.current[i] = mesh)} castShadow>
          <icosahedronGeometry args={[0.075, 0]} />
          <Solid color={i === WRONG ? colors.error : colors.lime} />
        </mesh>
      ))}
      <mesh ref={falling} castShadow>
        <icosahedronGeometry args={[0.08, 0]} />
        <Solid color={colors.error} />
      </mesh>
    </group>
  );
}
