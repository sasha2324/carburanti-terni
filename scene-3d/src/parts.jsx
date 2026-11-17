// Small building blocks shared by the five objects.
import { useMemo } from "react";
import { Quaternion, Vector3 } from "three";

/** Matte material with flat faces: the low-poly look. */
export function Solid({ color, ...rest }) {
  return <meshStandardMaterial color={color} roughness={0.8} metalness={0} flatShading {...rest} />;
}

/** See-through material for glass pipes and the storage tank. */
export function Glass({ color = "#d8d9da", opacity = 0.4 }) {
  return <meshStandardMaterial color={color} transparent opacity={opacity} roughness={0.15} depthWrite={false} />;
}

export function Box({ at, size, color, rotation }) {
  return (
    <mesh position={at} rotation={rotation} castShadow receiveShadow>
      <boxGeometry args={size} />
      <Solid color={color} />
    </mesh>
  );
}

export function Cylinder({ at, radius, height, color, segments = 10, rotation, radiusTop }) {
  return (
    <mesh position={at} rotation={rotation} castShadow receiveShadow>
      <cylinderGeometry args={[radiusTop ?? radius, radius, height, segments]} />
      <Solid color={color} />
    </mesh>
  );
}

const UP = new Vector3(0, 1, 0);

/** A round bar between two points in any direction: pipes, chutes, poles. */
export function Rod({ from, to, radius, color, glass = false, segments = 10 }) {
  const { position, quaternion, length } = useMemo(() => {
    const a = new Vector3(...from);
    const b = new Vector3(...to);
    const direction = b.clone().sub(a);
    return {
      position: a.clone().add(b).multiplyScalar(0.5),
      quaternion: new Quaternion().setFromUnitVectors(UP, direction.clone().normalize()),
      length: direction.length(),
    };
  }, [from, to]);
  return (
    <mesh position={position} quaternion={quaternion} castShadow={!glass} receiveShadow>
      <cylinderGeometry args={[radius, radius, length, segments]} />
      {glass ? <Glass /> : <Solid color={color} metalness={0.1} roughness={0.55} />}
    </mesh>
  );
}

/** A drop of data: a small low-poly gem. */
export function Drop({ at, color, size = 0.075 }) {
  return (
    <mesh position={at} castShadow>
      <icosahedronGeometry args={[size, 0]} />
      <Solid color={color} />
    </mesh>
  );
}

/** The low base under each step: a plain box, in the low-poly style. */
export function Pad({ color }) {
  return (
    <mesh position={[0, 0.06, 0]} receiveShadow>
      <boxGeometry args={[2.6, 0.12, 2.6]} />
      <Solid color={color} />
    </mesh>
  );
}
