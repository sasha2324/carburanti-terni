// The whole scene: an isometric camera, soft light and shadows, the five steps and the pipes.
// Step 1 of v2: objects only, nothing moves yet (frameloop "demand" draws only when needed).
import { useLayoutEffect, useMemo, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { Vector3 } from "three";
import { POSITIONS } from "./layout.js";
import { readPalette } from "./palette.js";
import Ministry from "./objects/Ministry.jsx";
import Pump from "./objects/Pump.jsx";
import Filter from "./objects/Filter.jsx";
import StorageTank from "./objects/StorageTank.jsx";
import PetrolStation from "./objects/PetrolStation.jsx";
import Pipeline from "./objects/Pipeline.jsx";

const NAMES = ["MIMIT", "Download", "Pulizia", "File JSON", "Sito"];

// How big the scene looks on screen, in scene units: the camera zooms so all of it fits.
const VIEW = { width: 21.8, height: 7.6 };
const LOOK_AT = [0, 0.1, 0];

// Where each name goes: in front of the step, on the ground.
const LABEL_POINTS = POSITIONS.map(([x, , z]) => new Vector3(x + 1.4, 0, z + 1.4));

/** Zooms the camera to fit, and tells the page where the names go on screen. */
function FitCamera({ onLabels }) {
  const camera = useThree((state) => state.camera);
  const size = useThree((state) => state.size);
  const invalidate = useThree((state) => state.invalidate);
  useLayoutEffect(() => {
    camera.zoom = Math.min(size.width / VIEW.width, size.height / VIEW.height);
    camera.lookAt(...LOOK_AT);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    onLabels(
      LABEL_POINTS.map((point) => {
        const p = point.clone().project(camera);
        return { left: ((p.x + 1) / 2) * size.width, top: ((1 - p.y) / 2) * size.height };
      })
    );
    invalidate();
  }, [camera, size, invalidate, onLabels]);
  return null;
}

/** The ground only shows the shadows: the page's mint panel stays visible behind. */
function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[60, 60]} />
      <shadowMaterial opacity={0.13} />
    </mesh>
  );
}

export default function App({ numbers }) {
  const colors = useMemo(() => readPalette(), []);
  const [labels, setLabels] = useState([]);
  const objects = [
    <Ministry colors={colors} />,
    <Pump colors={colors} />,
    <Filter colors={colors} />,
    <StorageTank colors={colors} days={numbers.days} />,
    <PetrolStation colors={colors} prices={numbers.cheapest} date={numbers.generated_text.split(",")[0]} />,
  ];

  return (
    <div className="scena-tela">
      <Canvas
        shadows="percentage"
        orthographic
        flat
        frameloop="demand"
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        camera={{ position: [20, 20, 20], near: 0.1, far: 100, zoom: 40 }}
      >
        <FitCamera onLabels={setLabels} />
        <hemisphereLight args={["#ffffff", colors.mint200, 1.5]} />
        <directionalLight
          position={[-6, 14, 9]}
          intensity={2.4}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-radius={5}
          shadow-bias={-0.0004}
          shadow-normalBias={0.03}
          shadow-camera-left={-13}
          shadow-camera-right={13}
          shadow-camera-top={13}
          shadow-camera-bottom={-13}
          shadow-camera-near={1}
          shadow-camera-far={45}
        />
        <Ground />
        <Pipeline colors={colors} />
        {objects.map((object, i) => (
          <group key={NAMES[i]} position={POSITIONS[i]}>
            {object}
          </group>
        ))}
      </Canvas>

      {/* the names of the steps: normal page text, placed over the scene */}
      <ol className="scena-etichette">
        {labels.map((spot, i) => (
          <li key={NAMES[i]} className="scena-etichetta" style={{ left: spot.left, top: spot.top }}>
            {NAMES[i]}
          </li>
        ))}
      </ol>
    </div>
  );
}
