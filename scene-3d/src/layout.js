// Where the five steps stand. Two layouts, the same camera:
// - row (from 768px): on a diagonal that the isometric camera shows from left to right;
// - column (phones): on the other diagonal, shown from top to bottom. Every object is
//   turned by 90°, so its pipes still meet: out at its front, in from its side.
export const STEP = 3;

/** Height of the pipes above the ground. */
export const PIPE_Y = 0.45;

/** Distance from the centre of a step to where its pipes start or end. */
export const CONNECT = 1.0;

/** Top of the low base (pad) under each step. */
export const BASE = 0.12;

const steps = [-2, -1, 0, 1, 2];

export const LAYOUTS = {
  row: {
    name: "row",
    turn: 0,
    positions: steps.map((i) => [STEP * i, 0, -STEP * i]),
    // the name of each step: in front of it, on the ground
    labelOffset: [1.4, 0, 1.4],
  },
  column: {
    name: "column",
    turn: -Math.PI / 2,
    positions: steps.map((i) => [STEP * i, 0, STEP * i]),
    // the name of each step: on its right, on the ground
    labelOffset: [1.75, 0, -1.75],
  },
};

/** A point of an object (its own directions) in scene directions, for an object turned by `turn`. */
export function turnPoint([x, y, z], turn) {
  const c = Math.cos(turn);
  const s = Math.sin(turn);
  return [x * c + z * s, y, -x * s + z * c];
}

/**
 * The pipe from one step to the next: out of the first one (its own +x side), an elbow,
 * into the next one (its own +z side). A zig-zag that reads well in the isometric view.
 */
export function route(from, to, layout) {
  const out = turnPoint([CONNECT, 0, 0], layout.turn);
  const inlet = turnPoint([0, 0, CONNECT], layout.turn);
  const start = [from[0] + out[0], PIPE_Y, from[2] + out[2]];
  const end = [to[0] + inlet[0], PIPE_Y, to[2] + inlet[2]];
  const elbow = Math.abs(out[0]) > 1e-6 ? [end[0], PIPE_Y, start[2]] : [start[0], PIPE_Y, end[2]];
  return { start, elbow, end, out, inlet };
}

// The bin of the wrong prices, next to the filter (step 3, at the centre of both layouts).
// These points are in the filter's own directions: turn them with `turnPoint`.
export const BIN = { x: 0.88, z: 0.85, size: 0.5, height: 0.34 };
export const CHUTE = {
  from: [0.3, BASE + 0.55, 0.28],
  to: [BIN.x - 0.12, BASE + BIN.height + 0.04, BIN.z - 0.12],
};
export const BIN_BOTTOM = [BIN.x, BASE + 0.12, BIN.z];
