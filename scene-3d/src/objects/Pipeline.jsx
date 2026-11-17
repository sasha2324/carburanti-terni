// The pipes between the steps (see `route` in layout.js).
// The two "Download" pipes (Ministry → pump → filter) are glass, to show the drops inside (Flow.jsx).
import { route } from "../layout.js";
import { Box, Rod, Solid } from "../parts.jsx";

const GLASS_ROUTES = [0, 1];

/** A point moved along a direction (a unit vector scaled to CONNECT) by `k` of its length. */
const shift = (point, direction, k) => [point[0] + direction[0] * k, point[1], point[2] + direction[2] * k];

export default function Pipeline({ colors, layout }) {
  const { positions } = layout;
  return (
    <group>
      {positions.slice(0, -1).map((from, i) => {
        const r = route(from, positions[i + 1], layout);
        const glass = GLASS_ROUTES.includes(i);
        return (
          <group key={i}>
            <Rod from={r.start} to={r.elbow} radius={0.13} color={colors.pipe} glass={glass} />
            <Rod from={r.elbow} to={r.end} radius={0.13} color={colors.pipe} glass={glass} />
            <mesh position={r.elbow} castShadow>
              <sphereGeometry args={[0.15, 10, 8]} />
              <Solid color={colors.pipe} />
            </mesh>
            {/* a small post under the elbow */}
            <Box at={[r.elbow[0], r.elbow[1] / 2, r.elbow[2]]} size={[0.1, r.elbow[1], 0.1]} color={colors.pipe} />
            {/* flanges where the pipe meets a step */}
            <Rod from={shift(r.start, r.out, -0.03)} to={shift(r.start, r.out, 0.03)} radius={0.18} color={colors.primary} />
            <Rod from={shift(r.end, r.inlet, -0.03)} to={shift(r.end, r.inlet, 0.03)} radius={0.18} color={colors.primary} />
          </group>
        );
      })}
    </group>
  );
}
