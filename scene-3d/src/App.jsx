// The whole scene: an isometric camera, soft light and shadows, the five steps and the pipes.
// Hover (or keyboard focus) lights an object up; a click moves the camera close and opens
// the panel of that step, with the real numbers. The panels are normal page HTML made by
// Python (sito/templates/_path_panels.html): this file only shows the chosen one.
// Steps in a row from 768px, in a column on phones; light objects in both themes.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Vector3 } from "three";
import CameraRig from "./CameraRig.jsx";
import Selectable from "./Selectable.jsx";
import { LAYOUTS } from "./layout.js";
import { MotionContext } from "./motion.js";
import { scenePalette } from "./palette.js";
import Ministry from "./objects/Ministry.jsx";
import Pump from "./objects/Pump.jsx";
import Filter from "./objects/Filter.jsx";
import StorageTank from "./objects/StorageTank.jsx";
import PetrolStation from "./objects/PetrolStation.jsx";
import Pipeline from "./objects/Pipeline.jsx";
import Flow from "./objects/Flow.jsx";

// On wide screens the panel covers the right part of the scene: 20rem + margins (style.css).
const PANEL_SIDE = 344;

/** The ground only shows the shadows: the page's mint panel stays visible behind. */
function Ground({ opacity }) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[60, 60]} />
      <shadowMaterial opacity={opacity} />
    </mesh>
  );
}

/** true while a media query matches (it can change while the page is open). */
function useMedia(text) {
  const query = useMemo(() => matchMedia(text), [text]);
  const [matches, setMatches] = useState(query.matches);
  useEffect(() => {
    const update = () => setMatches(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, [query]);
  return matches;
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

/** The step in the address (#passo-3 → 2), so a link can open a step directly. */
function stepFromAddress(count) {
  const match = location.hash.match(/^#passo-(\d)$/);
  const n = match ? Number(match[1]) - 1 : -1;
  return n >= 0 && n < count ? n : null;
}

/**
 * Shows the chosen panel (or none), and wires its buttons: Back/Next and close.
 * The panels are outside React, in the page made by Python.
 */
function usePanels(box, selected, choose) {
  const panels = useMemo(() => Array.from(box.querySelectorAll(".passo-dettagli")), [box]);
  const previous = useRef(selected);

  useEffect(() => {
    box.querySelectorAll(".passo-azioni, [data-chiudi]").forEach((element) => (element.hidden = false));
    const onClick = (event) => {
      const go = event.target.closest("[data-vai]");
      if (go) choose(Number(go.dataset.vai), { focus: go.classList.contains("avanti") ? "avanti" : "indietro" });
      if (event.target.closest("[data-chiudi]")) choose(null, { focus: "name" });
    };
    box.addEventListener("click", onClick);
    return () => box.removeEventListener("click", onClick);
  }, [box, choose]);

  useEffect(() => {
    box.hidden = selected == null;
    box.dataset.direzione = selected != null && previous.current != null && selected < previous.current ? "indietro" : "avanti";
    panels.forEach((panel, i) => {
      panel.hidden = i !== selected;
      panel.classList.remove("entra");
    });
    if (selected != null) {
      void panels[selected].offsetWidth; // restart the entrance animation
      panels[selected].classList.add("entra");
    }
    previous.current = selected;
    const address = selected == null ? location.pathname + location.search : `#${panels[selected].id}`;
    history.replaceState(null, "", address);
  }, [box, panels, selected]);

  return panels;
}

export default function App({ numbers, panelBox }) {
  const dark = useMedia("(prefers-color-scheme: dark)");
  const colors = useMemo(() => scenePalette(dark), [dark]);
  // From 768px the steps stand in a row, on phones in a column (the same breakpoint as style.css).
  const layout = useMedia("(min-width: 48rem)") ? LAYOUTS.row : LAYOUTS.column;
  const labelPoints = useMemo(
    () => layout.positions.map(([x, , z]) => new Vector3(x + layout.labelOffset[0], 0, z + layout.labelOffset[2])),
    [layout]
  );
  const names = useMemo(() => Array.from(panelBox.querySelectorAll(".passo-dettagli"), (p) => p.dataset.nome), [panelBox]);
  const [selected, setSelected] = useState(() => stepFromAddress(names.length));
  const [hovered, setHovered] = useState(null);
  const [paused, setPaused] = useState(false);
  const box = useRef();
  const labels = useRef([]);
  const still = useMedia("(prefers-reduced-motion: reduce)");
  const wide = useMedia("(min-width: 64rem)");
  const onScreen = useOnScreen(box);
  const moving = !still && !paused && onScreen;
  const motion = useMemo(() => ({ still, moving }), [still, moving]);
  const side = wide && selected != null ? PANEL_SIDE : 0;

  const current = useRef(selected);
  current.current = selected;

  // Choose a step (or null for the overview). `focus` says where the keyboard focus goes next.
  const choose = useCallback(
    (index, { focus } = {}) => {
      const before = current.current;
      setSelected(index);
      // After the page has shown the new panel:
      requestAnimationFrame(() => {
        if (focus === "name" && before != null) labels.current[before]?.focus();
        if (focus === "avanti" || focus === "indietro") {
          const buttons = Array.from(panelBox.querySelectorAll(`#passo-${index + 1} [data-vai]`));
          const same = buttons.find((b) => b.classList.contains("avanti") === (focus === "avanti"));
          (same || buttons[0])?.focus();
        }
        // On narrow screens the panel is under the scene: bring it into view.
        if (index != null && focus !== "name" && !wide) {
          panelBox.scrollIntoView({ block: "nearest", behavior: still ? "auto" : "smooth" });
        }
      });
    },
    [panelBox, wide, still]
  );

  usePanels(panelBox, selected, choose);

  // Esc closes the panel and puts the focus back on the name of that step.
  useEffect(() => {
    if (selected == null) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") choose(null, { focus: "name" });
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [selected, choose]);

  // The hand cursor over an object you can click.
  useEffect(() => {
    document.body.style.cursor = hovered != null ? "pointer" : "";
    return () => (document.body.style.cursor = "");
  }, [hovered]);

  const objects = [
    <Ministry colors={colors} />,
    <Pump colors={colors} />,
    <Filter colors={colors} />,
    <StorageTank colors={colors} days={numbers.days} turn={layout.turn} />,
    <PetrolStation colors={colors} prices={numbers.cheapest} date={numbers.generated_text.split(",")[0]} turn={layout.turn} />,
  ];

  const onNameKey = (event, i) => {
    const keys = { ArrowRight: i + 1, ArrowDown: i + 1, ArrowLeft: i - 1, ArrowUp: i - 1, Home: 0, End: names.length - 1 };
    if (!(event.key in keys)) return;
    event.preventDefault();
    const next = Math.min(Math.max(keys[event.key], 0), names.length - 1);
    choose(next);
    labels.current[next]?.focus();
  };

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
        onPointerMissed={(event) => event.button === 0 && choose(null)}
      >
        <MotionContext.Provider value={motion}>
          <CameraRig selected={selected} side={side} layout={layout} labelPoints={labelPoints} labels={labels} />
          <hemisphereLight args={[colors.sky, colors.groundLight, 1.5]} />
          <directionalLight
            position={[-6, 14, 9]}
            intensity={colors.sun}
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
          <Ground opacity={colors.shadow} />
          <Pipeline colors={colors} layout={layout} />
          <Flow colors={colors} layout={layout} />
          {objects.map((object, i) => (
            <group key={names[i]} position={layout.positions[i]} rotation={[0, layout.turn, 0]}>
              <Selectable index={i} glow={hovered === i ? 0.55 : selected === i ? 0.3 : 0} onHover={setHovered} onChoose={choose}>
                {object}
              </Selectable>
            </group>
          ))}
        </MotionContext.Provider>
      </Canvas>

      {/* the names of the steps: real buttons over the scene, so the keyboard works too */}
      <ol className="scena-etichette">
        {names.map((name, i) => (
          <li key={name}>
            <button
              type="button"
              ref={(element) => (labels.current[i] = element)}
              className="scena-etichetta"
              aria-controls={`passo-${i + 1}`}
              aria-expanded={selected === i}
              onClick={() => choose(selected === i ? null : i)}
              onKeyDown={(event) => onNameKey(event, i)}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              onFocus={() => setHovered(i)}
              onBlur={() => setHovered(null)}
            >
              {name}
            </button>
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
