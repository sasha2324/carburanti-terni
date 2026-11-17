// The pipes between the steps. From one step the pipe goes along x, turns at an elbow,
// then goes along z into the next step: a zig-zag that reads well in the isometric view.
// The two "Download" pipes (Ministry → pump → filter) are glass, to show the drops inside.
import { PIPE_Y, CONNECT, POSITIONS } from "../layout.js";
import { Box, Drop, Rod, Solid } from "../parts.jsx";

const GLASS_ROUTES = [0, 1];

function route(from, to) {
  const start = [from[0] + CONNECT, PIPE_Y, from[2]];
  const elbow = [to[0], PIPE_Y, from[2]];
  const end = [to[0], PIPE_Y, to[2] + CONNECT];
  return { start, elbow, end };
}

/** A point at `t` (0…1) along the route, through the elbow. */
function along({ start, elbow, end }, t) {
  const first = Math.abs(elbow[0] - start[0]);
  const second = Math.abs(elbow[2] - end[2]);
  const d = t * (first + second);
  if (d <= first) return [start[0] + d, PIPE_Y, start[2]];
  return [elbow[0], PIPE_Y, elbow[2] - (d - first)];
}

export default function Pipeline({ colors }) {
  return (
    <group>
      {POSITIONS.slice(0, -1).map((from, i) => {
        const r = route(from, POSITIONS[i + 1]);
        const glass = GLASS_ROUTES.includes(i);
        return (
          <group key={i}>
            <Rod from={r.start} to={r.elbow} radius={0.13} color={colors.hairlineStrong} glass={glass} />
            <Rod from={r.elbow} to={r.end} radius={0.13} color={colors.hairlineStrong} glass={glass} />
            <mesh position={r.elbow} castShadow>
              <sphereGeometry args={[0.15, 10, 8]} />
              <Solid color={colors.hairlineStrong} />
            </mesh>
            {/* a small post under the elbow */}
            <Box at={[r.elbow[0], PIPE_Y / 2, r.elbow[2]]} size={[0.1, PIPE_Y, 0.1]} color={colors.hairlineStrong} />
            {/* flanges where the pipe meets a step */}
            {[r.start, r.end].map((at, k) => (
              <Rod
                key={k}
                from={k === 0 ? [at[0] - 0.03, at[1], at[2]] : [at[0], at[1], at[2] + 0.03]}
                to={k === 0 ? [at[0] + 0.03, at[1], at[2]] : [at[0], at[1], at[2] - 0.03]}
                radius={0.18}
                color={colors.primary}
              />
            ))}
            {glass && [0.18, 0.42, 0.66, 0.88].map((t) => <Drop key={t} at={along(r, t)} color={colors.lime} />)}
          </group>
        );
      })}
    </group>
  );
}
