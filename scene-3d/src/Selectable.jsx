// One step of the scene that reacts to the pointer: it lights up when the pointer
// (or the keyboard focus on its name) is on it, and a click chooses it.
import { useLayoutEffect, useRef } from "react";
import { useThree } from "@react-three/fiber";

const GLOW = "#b7ecda"; // mint-200: a soft light, in the colours of the site

/** `glow`: 0 = normal, about 0.3 = chosen, about 0.55 = under the pointer or the focus. */
export default function Selectable({ index, glow, onHover, onChoose, children }) {
  const lit = glow > 0;
  const group = useRef();
  const invalidate = useThree((state) => state.invalidate);

  useLayoutEffect(() => {
    group.current.traverse((object) => {
      const material = object.material;
      if (!material || !("emissive" in material)) return;
      material.emissive.set(lit ? GLOW : "#000000");
      material.emissiveIntensity = glow;
    });
    invalidate();
  }, [lit, glow, invalidate]);

  return (
    <group
      ref={group}
      onPointerOver={(event) => {
        event.stopPropagation();
        onHover(index);
      }}
      onPointerOut={() => onHover(null)}
      onClick={(event) => {
        event.stopPropagation();
        onChoose(index);
      }}
    >
      {children}
    </group>
  );
}
