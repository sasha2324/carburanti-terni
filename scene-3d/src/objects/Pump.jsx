// Step 2, Download: a pump with a valve, between the Ministry and the filter.
import { useRef } from "react";
import { PIPE_Y, CONNECT } from "../layout.js";
import { useTicker } from "../motion.js";
import { Box, Cylinder, Pad, Rod, Solid } from "../parts.jsx";

export default function Pump({ colors }) {
  const wheel = useRef();
  // The valve wheel turns slowly while the data flows.
  useTicker((time) => {
    wheel.current.rotation.y = time * 0.9;
  });

  return (
    <group>
      <Pad color={colors.white} />
      <Box at={[0, 0.16, 0]} size={[1.2, 0.08, 1.0]} color={colors.mint200} />

      {/* the motor, lying down, with green ends */}
      <Cylinder at={[-0.1, PIPE_Y, 0]} radius={0.25} height={0.8} rotation={[0, 0, Math.PI / 2]} color={colors.white} />
      {[-0.52, 0.32].map((x) => (
        <Cylinder key={x} at={[x, PIPE_Y, 0]} radius={0.27} height={0.06} rotation={[0, 0, Math.PI / 2]} color={colors.primary} />
      ))}

      {/* in from the Ministry (+z), out to the filter (+x) */}
      <Rod from={[0, PIPE_Y, 0.22]} to={[0, PIPE_Y, CONNECT]} radius={0.13} color={colors.hairlineStrong} />
      <Rod from={[0.3, PIPE_Y, 0]} to={[CONNECT, PIPE_Y, 0]} radius={0.13} color={colors.hairlineStrong} />

      {/* the valve wheel on the pipe, with three spokes so you can see it turn */}
      <Rod from={[0, PIPE_Y, 0.62]} to={[0, PIPE_Y + 0.38, 0.62]} radius={0.03} color={colors.body} />
      <group ref={wheel} position={[0, PIPE_Y + 0.38, 0.62]}>
        <mesh rotation={[Math.PI / 2, 0, 0]} castShadow>
          <torusGeometry args={[0.17, 0.03, 6, 12]} />
          <Solid color={colors.primary} />
        </mesh>
        {[0, 1, 2].map((k) => (
          <Box key={k} at={[0, 0, 0]} size={[0.32, 0.025, 0.025]} rotation={[0, (k * Math.PI) / 3, 0]} color={colors.primary} />
        ))}
      </group>
    </group>
  );
}
