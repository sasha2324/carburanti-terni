// Step 1, MIMIT: the Ministry building, and the tank its two CSV files come from.
import { useMemo } from "react";
import { Box, Cylinder, Pad, Solid } from "../parts.jsx";
import { plateTexture } from "../signs.js";

const BASE = 0.12; // top of the pad

export default function Ministry({ colors }) {
  const sign = useMemo(() => plateTexture("MIMIT", { background: colors.white, color: colors.forest }), [colors]);
  const building = { x: -0.35, z: -0.15, w: 1.4, h: 1.4, d: 1.3 };
  const front = building.z + building.d / 2 + 0.011; // the face towards the camera (+z)
  const side = building.x + building.w / 2 + 0.011; // the other visible face (+x)

  return (
    <group>
      <Pad color={colors.white} />

      {/* the building */}
      <Box at={[building.x, BASE + building.h / 2, building.z]} size={[building.w, building.h, building.d]} color={colors.white} />
      <Box at={[building.x, BASE + building.h + 0.06, building.z]} size={[building.w + 0.14, 0.12, building.d + 0.14]} color={colors.mint200} />
      {[-0.8, -0.35].map((x) => (
        <Box key={`a${x}`} at={[x, 0.75, front]} size={[0.24, 0.2, 0.02]} color={colors.primary} />
      ))}
      {[-0.8, -0.35, 0.1].map((x) => (
        <Box key={`b${x}`} at={[x, 1.08, front]} size={[0.24, 0.2, 0.02]} color={colors.primary} />
      ))}
      <Box at={[0.1, BASE + 0.22, front]} size={[0.26, 0.44, 0.02]} color={colors.forest} />
      {[-0.5, 0.05].map((z) =>
        [0.75, 1.08].map((y) => <Box key={`s${z}${y}`} at={[side, y, z]} size={[0.02, 0.2, 0.24]} color={colors.primary} />)
      )}
      <mesh position={[building.x, 1.36, front + 0.001]}>
        <planeGeometry args={[1.15, 0.26]} />
        <meshBasicMaterial map={sign} toneMapped={false} />
      </mesh>

      {/* the tank with the data, where the pipe starts */}
      <Cylinder at={[0.75, BASE + 0.5, 0.05]} radius={0.36} height={1.0} color={colors.white} />
      <Cylinder at={[0.75, BASE + 0.82, 0.05]} radius={0.375} height={0.1} color={colors.primary} />
      <mesh position={[0.75, BASE + 1.0, 0.05]} castShadow>
        <sphereGeometry args={[0.36, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <Solid color={colors.white} />
      </mesh>
    </group>
  );
}
