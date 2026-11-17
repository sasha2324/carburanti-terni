// Where the five steps stand: on a diagonal, 3 units apart along x and along z.
// From the isometric camera they read from left to right.
export const STEP = 3;

/** Height of the pipes above the ground. */
export const PIPE_Y = 0.45;

/** Distance from the centre of a step to where its pipes start or end. */
export const CONNECT = 1.0;

/** Top of the low base (pad) under each step. */
export const BASE = 0.12;

export const POSITIONS = [-2, -1, 0, 1, 2].map((i) => [STEP * i, 0, -STEP * i]);

/**
 * The pipe from one step to the next: along x, an elbow, then along z.
 * A zig-zag that reads well in the isometric view.
 */
export function route(from, to) {
  return {
    start: [from[0] + CONNECT, PIPE_Y, from[2]],
    elbow: [to[0], PIPE_Y, from[2]],
    end: [to[0], PIPE_Y, to[2] + CONNECT],
  };
}

// The bin of the wrong prices, next to the filter (step 3, at POSITIONS[2] = the origin).
export const BIN = { x: 0.88, z: 0.85, size: 0.5, height: 0.34 };
export const CHUTE = {
  from: [0.3, BASE + 0.55, 0.28],
  to: [BIN.x - 0.12, BASE + BIN.height + 0.04, BIN.z - 0.12],
};
export const BIN_BOTTOM = [BIN.x, BASE + 0.12, BIN.z];
