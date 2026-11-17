// The pipes between the steps (see `route` in layout.js).
// The two "Download" pipes (Ministry → pump → filter) are glass, to show the drops inside (Flow.jsx).
import { POSITIONS, route } from "../layout.js";
import { Box, Rod, Solid } from "../parts.jsx";

const GLASS_ROUTES = [0, 1];

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
            <Box at={[r.elbow[0], r.elbow[1] / 2, r.elbow[2]]} size={[0.1, r.elbow[1], 0.1]} color={colors.hairlineStrong} />
            {/* flanges where the pipe meets a step */}
            <Rod from={[r.start[0] - 0.03, r.start[1], r.start[2]]} to={[r.start[0] + 0.03, r.start[1], r.start[2]]} radius={0.18} color={colors.primary} />
            <Rod from={[r.end[0], r.end[1], r.end[2] + 0.03]} to={[r.end[0], r.end[1], r.end[2] - 0.03]} radius={0.18} color={colors.primary} />
          </group>
        );
      })}
    </group>
  );
}
