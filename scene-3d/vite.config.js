import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The 3D scene of come-funziona-3d.html. The page itself is made by Python (sito/build.py):
// Vite only makes the JavaScript, with fixed names so the page can point to it.
export default defineConfig({
  plugins: [react()],
  input: "src/main.jsx",
  build: {
    outDir: "../sito/static/scene-3d",
    emptyOutDir: true,
    rolldownOptions: {
      output: {
        entryFileNames: "scene.js",
        chunkFileNames: "[name].js",
        assetFileNames: "[name][extname]",
      },
    },
  },
});
