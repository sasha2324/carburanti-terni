import { createRoot } from "react-dom/client";
import App from "./App.jsx";

// The real numbers, written into the page by Python (sito/build.py → how-it-works-3d.html).
const numbers = JSON.parse(document.getElementById("numeri-3d").textContent);
const container = document.getElementById("scena-3d");

// The price sign is drawn with the site's font (Jost): wait for it, at most one second.
const fontReady = Promise.race([
  document.fonts.load('600 48px "Jost"'),
  new Promise((resolve) => setTimeout(resolve, 1000)),
]);

fontReady.then(() => {
  container.textContent = "";
  createRoot(container).render(<App numbers={numbers} />);
});
