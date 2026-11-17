// Step 4, the JSON file: a glass storage tank. The level is real: saved days out of a year.
// When the scene starts, the tank fills up to that level; then small bubbles rise inside.
import { useMemo, useRef } from "react";
import { CONNECT, PIPE_Y } from "../layout.js";
import { easeOutCubic, useTicker } from "../motion.js";
import { Cylinder, Glass, Pad, Rod, Solid } from "../parts.jsx";
import { plateTexture } from "../signs.js";

const BOTTOM = 0.2;
const HEIGHT = 1.5;
const RADIUS = 0.7;
const FILL_SECONDS = 2.2;
const BUBBLES = 6;

// `turn`: how much the layout turned this object; the plate turns back, so it always faces the camera.
export default function StorageTank({ colors, days, turn = 0 }) {
  const target = (HEIGHT - 0.06) * Math.min(Math.max(days / 365, 0.06), 1);
  const plate = useMemo(() => plateTexture("{ } JSON", { background: colors.white, color: colors.primaryDeep }), [colors]);
  const liquid = useRef();
  const bubbles = useRef([]);

  useTicker((time) => {
    const level = Math.max(target * easeOutCubic(time / FILL_SECONDS), 0.001);
    liquid.current.scale.y = level;
    liquid.current.position.y = BOTTOM + 0.03 + level / 2;
    bubbles.current.forEach((bubble, k) => {
      const rise = (time * 0.32 + k / BUBBLES) % 1;
      const angle = k * 2.1;
      bubble.position.set(Math.cos(angle) * 0.38, BOTTOM + 0.08 + rise * (level - 0.12), Math.sin(angle) * 0.38);
      bubble.visible = level > 0.2;
    });
  });

  return (
    <group>
      <Pad color={colors.pad} />
      <Cylinder at={[0, BOTTOM - 0.04, 0]} radius={RADIUS + 0.06} height={0.08} color={colors.mint200} />

      {/* in from the filter (+z, enters the glass), out to the petrol station (+x) */}
      <Rod from={[0, PIPE_Y, 0.4]} to={[0, PIPE_Y, CONNECT]} radius={0.13} color={colors.hairlineStrong} />
      <Rod from={[RADIUS - 0.05, PIPE_Y, 0]} to={[CONNECT, PIPE_Y, 0]} radius={0.13} color={colors.hairlineStrong} />

      {/* the data inside (a cylinder 1 unit tall, scaled to the level), then the glass around it */}
      <mesh ref={liquid} castShadow>
        <cylinderGeometry args={[RADIUS - 0.04, RADIUS - 0.04, 1, 14]} />
        <Solid color={colors.lime} />
      </mesh>
      {Array.from({ length: BUBBLES }, (_, k) => (
        <mesh key={k} ref={(mesh) => (bubbles.current[k] = mesh)}>
          <icosahedronGeometry args={[0.04, 0]} />
          <Solid color={colors.white} />
        </mesh>
      ))}
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

      {/* the plate, on the side of the tank that faces the camera */}
      <mesh
        position={[0.75 * Math.sin(Math.PI / 4 - turn), BOTTOM + HEIGHT * 0.78, 0.75 * Math.cos(Math.PI / 4 - turn)]}
        rotation={[0, Math.PI / 4 - turn, 0]}
      >
        <planeGeometry args={[0.84, 0.21]} />
        <meshBasicMaterial map={plate} toneMapped={false} />
      </mesh>
    </group>
  );
}
