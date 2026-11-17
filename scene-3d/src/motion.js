// Shared rules for everything that moves in the scene.
import { createContext, useContext, useLayoutEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";

/** `still`: the visitor asked for less motion, so the scene is a still image. */
export const MotionContext = createContext({ still: false });

// With "reduce motion" every object is shown as it is at the end (full tank, final prices).
const FINAL_TIME = 600;

/**
 * Calls `apply(seconds)` on every frame while the scene moves.
 * The time only grows while frames are drawn: after a pause (or after scrolling away)
 * everything goes on from where it stopped, without jumping.
 */
export function useTicker(apply) {
  const { still } = useContext(MotionContext);
  const time = useRef(0);
  const latest = useRef(apply);
  latest.current = apply;
  const invalidate = useThree((state) => state.invalidate);

  useLayoutEffect(() => {
    latest.current(still ? FINAL_TIME : time.current);
    invalidate();
  }, [still, invalidate]);

  useFrame((_, delta) => {
    if (still) return;
    time.current += Math.min(delta, 0.1);
    latest.current(time.current);
  });
}

/** Fast start, soft end (kinetics.colorion.co, "Odometer Count-up": ease-out cubic). */
export const easeOutCubic = (x) => 1 - (1 - Math.min(Math.max(x, 0), 1)) ** 3;

/** Slow start, then faster: for things that fall. */
export const easeInQuad = (x) => Math.min(Math.max(x, 0), 1) ** 2;
