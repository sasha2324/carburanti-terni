// Step 5, the website: a petrol station. Its sign shows the real cheapest prices.
import { useMemo } from "react";
import { PIPE_Y, CONNECT } from "../layout.js";
import { Box, Cylinder, Pad, Rod } from "../parts.jsx";
import { priceSignTexture } from "../signs.js";

const BASE = 0.12;

export default function PetrolStation({ colors, prices, date }) {
  const sign = useMemo(() => priceSignTexture({ prices, date, colors }), [prices, date, colors]);

  return (
    <group>
      <Pad color={colors.white} />

      {/* the canopy on two columns */}
      {[-0.62, 0.62].map((x) => (
        <Cylinder key={x} at={[x, BASE + 0.62, -0.1]} radius={0.06} height={1.24} segments={8} color={colors.hairlineStrong} />
      ))}
      <Box at={[0, BASE + 1.24, -0.1]} size={[1.9, 0.1, 1.4]} color={colors.primary} />
      <Box at={[0, BASE + 1.33, -0.1]} size={[1.86, 0.1, 1.36]} color={colors.white} />

      {/* the island with two pumps */}
      <Box at={[0, BASE + 0.05, -0.1]} size={[1.5, 0.1, 0.36]} color={colors.mint200} />
      {[-0.32, 0.32].map((x) => (
        <group key={x} position={[x, BASE + 0.1, -0.1]}>
          <Box at={[0, 0.27, 0]} size={[0.26, 0.54, 0.2]} color={colors.white} />
          <Box at={[0, 0.5, 0]} size={[0.27, 0.08, 0.21]} color={colors.primary} />
          <Box at={[0, 0.34, 0.101]} size={[0.16, 0.1, 0.01]} color={colors.forest} />
        </group>
      ))}

      {/* the pipe from the storage tank goes down into the ground (+z) */}
      <Rod from={[0, PIPE_Y, CONNECT]} to={[0, PIPE_Y, 0.82]} radius={0.13} color={colors.hairlineStrong} />
      <Rod from={[0, PIPE_Y + 0.1, 0.82]} to={[0, BASE, 0.82]} radius={0.13} color={colors.hairlineStrong} />
      <Cylinder at={[0, BASE + 0.02, 0.82]} radius={0.22} height={0.04} color={colors.mint200} />

      {/* the price sign, turned towards the camera */}
      <group position={[0.95, BASE, 0.62]} rotation={[0, Math.PI / 4, 0]}>
        <Box at={[0, 0.06, 0]} size={[0.44, 0.12, 0.2]} color={colors.mint200} />
        <Box at={[0, 0.82, 0]} size={[0.6, 1.4, 0.1]} color={colors.white} />
        <mesh position={[0, 0.84, 0.051]}>
          <planeGeometry args={[0.56, 1.12]} />
          <meshBasicMaterial map={sign} toneMapped={false} />
        </mesh>
      </group>
    </group>
  );
}
