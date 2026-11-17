import { createRoot } from "react-dom/client";
import App from "./App.jsx";

// The real numbers, written into the page by Python (sito/build.py → how-it-works-3d.html).
const numbers = JSON.parse(document.getElementById("numeri-3d").textContent);
const container = document.getElementById("scena-3d");
const panelBox = document.getElementById("scena-pannelli");

/** Can this browser draw 3D? If not, the page keeps the simple list of the five steps. */
function canDraw3d() {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

if (!canDraw3d()) {
  container.querySelector(".scena-attesa").textContent = "Il tuo browser non mostra la scena 3D. Qui sotto trovi tutti i passi.";
} else {
  container.querySelector(".scena-attesa").textContent = "Carico la scena 3D…";
  // From here the panels open one at a time, on top of the scene or under it (style.css).
  document.documentElement.classList.add("con-scena");

  // The price sign is drawn with the site's font (Jost): wait for it, at most one second.
  const fontReady = Promise.race([
    document.fonts.load('600 48px "Jost"'),
    new Promise((resolve) => setTimeout(resolve, 1000)),
  ]);
  fontReady.then(() => {
    container.textContent = "";
    createRoot(container).render(<App numbers={numbers} panelBox={panelBox} />);
  });
}
