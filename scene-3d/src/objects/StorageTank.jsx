// Step 4, the JSON file: a glass storage tank. The level is real: saved days out of a year.
import { useMemo } from "react";
import { PIPE_Y, CONNECT } from "../layout.js";
import { Cylinder, Glass, Pad, Rod, Solid } from "../parts.jsx";
import { plateTexture } from "../signs.js";

const BOTTOM = 0.2;
const HEIGHT = 1.5;
const RADIUS = 0.7;

export default function StorageTank({ colors, days }) {
  const fill = Math.min(Math.max(days / 365, 0.06), 1);
  const liquid = (HEIGHT - 0.06) * fill;
  const plate = useMemo(() => plateTexture("{ } JSON", { background: colors.white, color: colors.primaryDeep }), [colors]);

  return (
    <group>
      <Pad color={colors.white} />
      <Cylinder at={[0, BOTTOM - 0.04, 0]} radius={RADIUS + 0.06} height={0.08} color={colors.mint200} />

      {/* in from the filter (+z, enters the glass), out to the petrol station (+x) */}
      <Rod from={[0, PIPE_Y, 0.4]} to={[0, PIPE_Y, CONNECT]} radius={0.13} color={colors.hairlineStrong} />
      <Rod from={[RADIUS - 0.05, PIPE_Y, 0]} to={[CONNECT, PIPE_Y, 0]} radius={0.13} color={colors.hairlineStrong} />

      {/* the data inside, then the glass around it */}
      <mesh position={[0, BOTTOM + 0.03 + liquid / 2, 0]} castShadow>
        <cylinderGeometry args={[RADIUS - 0.04, RADIUS - 0.04, liquid, 14]} />
        <Solid color={colors.lime} />
      </mesh>
      <mesh position={[0, BOTTOM + HEIGHT / 2, 0]}>
        <cylinderGeometry args={[RADIUS, RADIUS, HEIGHT, 14, 1, true]} />
        <Glass opacity={0.28} />
      </mesh>
      {[BOTTOM + 0.02, BOTTOM + HEIGHT - 0.02].map((y) => (
        <mesh key={y} position={[0, y, 0]} rotation={[Math.PI / 2, 0, 0]} castShadow>
          <torusGeometry args={[RADIUS, 0.035, 4, 24]} />
          <Solid color={colors.primary} />
        </mesh>
      ))}
      <Cylinder at={[0, BOTTOM + HEIGHT + 0.14, 0]} radius={RADIUS + 0.02} radiusTop={0.12} height={0.28} segments={14} color={colors.white} />

      {/* the plate, turned towards the camera */}
      <mesh position={[0.53, BOTTOM + HEIGHT * 0.78, 0.53]} rotation={[0, Math.PI / 4, 0]}>
        <planeGeometry args={[0.84, 0.21]} />
        <meshBasicMaterial map={plate} toneMapped={false} />
      </mesh>
    </group>
  );
}
