// The colours of the scene, from DESIGN.md (the light values).
// The objects stay light in both themes, like a white model: in dark mode only the bases,
// the light and the shadows change. (The page's CSS tokens are not read here: in dark mode
// they turn the text light, and the price sign would become unreadable.)
const LIGHT = {
  white: "#ffffff",
  pad: "#ffffff",
  mint100: "#e3faf2",
  mint200: "#b7ecda",
  primary: "#008254",
  primaryDeep: "#006642",
  forest: "#00482f",
  ink: "#000000",
  body: "#3d4045",
  muted: "#64666a",
  hairlineStrong: "#d8d9da",
  pipe: "#d8d9da",
  lime: "#a8ea4c",
  // Red only for what the cleaning throws away (DESIGN.md: "removal actions")
  error: "#de2828",
  // light and shadows
  sky: "#ffffff",
  groundLight: "#b7ecda",
  sun: 2.4,
  shadow: 0.13,
};

const DARK = {
  ...LIGHT,
  white: "#eef3f0", // a little less bright on a dark page
  pad: "#1c2722", // the bases become dark, so the objects stand out
  pipe: "#c9d2cd",
  groundLight: "#1c2722",
  sun: 2.1,
  shadow: 0.38,
};

export const scenePalette = (dark) => (dark ? DARK : LIGHT);
