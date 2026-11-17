// The whole scene: an isometric camera, soft light and shadows, the five steps and the pipes.
// Step 2 of v2: the movement. It runs only while the scene is on screen and not paused;
// with "reduce motion" the scene is a still image of the final state.
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { Vector3 } from "three";
import { POSITIONS } from "./layout.js";
import { MotionContext } from "./motion.js";
import { readPalette } from "./palette.js";
import Ministry from "./objects/Ministry.jsx";
import Pump from "./objects/Pump.jsx";
import Filter from "./objects/Filter.jsx";
import StorageTank from "./objects/StorageTank.jsx";
import PetrolStation from "./objects/PetrolStation.jsx";
import Pipeline from "./objects/Pipeline.jsx";
import Flow from "./objects/Flow.jsx";

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

/** true when the visitor asked their device for less motion (it can change while the page is open). */
function useReducedMotion() {
  const query = useMemo(() => matchMedia("(prefers-reduced-motion: reduce)"), []);
  const [reduced, setReduced] = useState(query.matches);
  useEffect(() => {
    const update = () => setReduced(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, [query]);
  return reduced;
}

/** true while at least a bit of the element is on screen: no drawing when nobody sees it. */
function useOnScreen(ref) {
  const [onScreen, setOnScreen] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => setOnScreen(entry.isIntersecting));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ref]);
  return onScreen;
}

export default function App({ numbers }) {
  const colors = useMemo(() => readPalette(), []);
  const [labels, setLabels] = useState([]);
  const [paused, setPaused] = useState(false);
  const box = useRef();
  const still = useReducedMotion();
  const onScreen = useOnScreen(box);
  const moving = !still && !paused && onScreen;
  const motion = useMemo(() => ({ still }), [still]);

  return (
    <div className="scena-tela" ref={box}>
      <Canvas
        shadows="percentage"
        orthographic
        flat
        frameloop={moving ? "always" : "demand"}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        camera={{ position: [20, 20, 20], near: 0.1, far: 100, zoom: 40 }}
      >
        <MotionContext.Provider value={motion}>
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
          <Flow colors={colors} />
          <group position={POSITIONS[0]}>
            <Ministry colors={colors} />
          </group>
          <group position={POSITIONS[1]}>
            <Pump colors={colors} />
          </group>
          <group position={POSITIONS[2]}>
            <Filter colors={colors} />
          </group>
          <group position={POSITIONS[3]}>
            <StorageTank colors={colors} days={numbers.days} />
          </group>
          <group position={POSITIONS[4]}>
            <PetrolStation colors={colors} prices={numbers.cheapest} date={numbers.generated_text.split(",")[0]} />
          </group>
        </MotionContext.Provider>
      </Canvas>

      {/* the names of the steps: normal page text, placed over the scene */}
      <ol className="scena-etichette">
        {labels.map((spot, i) => (
          <li key={NAMES[i]} className="scena-etichetta" style={{ left: spot.left, top: spot.top }}>
            {NAMES[i]}
          </li>
        ))}
      </ol>

      {/* moving things must be easy to stop; with "reduce motion" nothing moves, so no button */}
      {!still && (
        <button type="button" className="pulsante-contorno scena-pausa" onClick={() => setPaused((p) => !p)}>
          {paused ? "Riprendi" : "Pausa"}
        </button>
      )}
    </div>
  );
}
