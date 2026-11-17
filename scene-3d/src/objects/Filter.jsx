// Step 3, Cleaning: the filter. Wrong prices slide down a chute into a small bin.
import { PIPE_Y, CONNECT } from "../layout.js";
import { Box, Cylinder, Drop, Pad, Rod, Solid } from "../parts.jsx";

const BASE = 0.12;
const BIN = { x: 0.88, z: 0.85, size: 0.5, height: 0.34 };

export default function Filter({ colors }) {
  const wall = 0.03;
  const half = BIN.size / 2;
  return (
    <group>
      <Pad color={colors.white} />

      {/* the filter: a vessel with rings like a cartridge, and a funnel on top */}
      <Cylinder at={[0, BASE + 0.45, 0]} radius={0.48} height={0.9} color={colors.white} />
      {[0.3, 0.52, 0.74].map((y) => (
        <mesh key={y} position={[0, BASE + y, 0]} rotation={[Math.PI / 2, 0, 0]} castShadow>
          <torusGeometry args={[0.485, 0.018, 4, 20]} />
          <Solid color={colors.hairlineStrong} />
        </mesh>
      ))}
      <Cylinder at={[0, BASE + 1.07, 0]} radius={0.24} radiusTop={0.52} height={0.34} color={colors.mint200} />

      {/* in from the pump (+z), out to the storage tank (+x) */}
      <Rod from={[0, PIPE_Y, 0.46]} to={[0, PIPE_Y, CONNECT]} radius={0.13} color={colors.hairlineStrong} />
      <Rod from={[0.46, PIPE_Y, 0]} to={[CONNECT, PIPE_Y, 0]} radius={0.13} color={colors.hairlineStrong} />

      {/* the chute and the bin of the wrong prices */}
      <Rod from={[0.3, BASE + 0.55, 0.28]} to={[BIN.x - 0.12, BASE + BIN.height + 0.04, BIN.z - 0.12]} radius={0.05} color={colors.hairlineStrong} />
      <group position={[BIN.x, BASE, BIN.z]}>
        <Box at={[0, wall / 2, 0]} size={[BIN.size, wall, BIN.size]} color={colors.hairlineStrong} />
        <Box at={[0, BIN.height / 2, half]} size={[BIN.size, BIN.height, wall]} color={colors.hairlineStrong} />
        <Box at={[0, BIN.height / 2, -half]} size={[BIN.size, BIN.height, wall]} color={colors.hairlineStrong} />
        <Box at={[half, BIN.height / 2, 0]} size={[wall, BIN.height, BIN.size]} color={colors.hairlineStrong} />
        <Box at={[-half, BIN.height / 2, 0]} size={[wall, BIN.height, BIN.size]} color={colors.hairlineStrong} />
        <Box at={[0, BIN.height, half]} size={[BIN.size + 0.02, 0.04, wall + 0.02]} color={colors.error} />
        <Box at={[half, BIN.height, 0]} size={[wall + 0.02, 0.04, BIN.size + 0.02]} color={colors.error} />
        {[
          [-0.08, 0.1, 0.05],
          [0.09, 0.1, -0.06],
          [0.02, 0.18, 0.02],
        ].map((at) => (
          <Drop key={at.join()} at={at} color={colors.error} size={0.08} />
        ))}
      </group>
    </group>
  );
}
