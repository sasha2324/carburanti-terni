// Where the five steps stand: on a diagonal, 3 units apart along x and along z.
// From the isometric camera they read from left to right.
export const STEP = 3;

/** Height of the pipes above the ground. */
export const PIPE_Y = 0.45;

/** Distance from the centre of a step to where its pipes start or end. */
export const CONNECT = 1.0;

export const POSITIONS = [-2, -1, 0, 1, 2].map((i) => [STEP * i, 0, -STEP * i]);
