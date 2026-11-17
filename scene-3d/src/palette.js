// The colours of the scene come from the site's CSS tokens (style.css, DESIGN.md),
// so the 3D objects match the rest of the page.
export function readPalette() {
  const css = getComputedStyle(document.documentElement);
  const token = (name, fallback) => css.getPropertyValue(name).trim() || fallback;
  return {
    white: "#ffffff",
    canvasSoft: token("--canvas-soft", "#f7f7f7"),
    mint100: token("--mint-100", "#e3faf2"),
    mint200: token("--mint-200", "#b7ecda"),
    primary: token("--primary", "#008254"),
    primaryDeep: token("--primary-deep", "#006642"),
    forest: token("--forest", "#00482f"),
    ink: token("--ink", "#000000"),
    body: token("--body", "#3d4045"),
    muted: token("--muted", "#64666a"),
    hairline: token("--hairline", "#ebebec"),
    hairlineStrong: token("--hairline-strong", "#d8d9da"),
    lime: token("--lime-ribbon", "#a8ea4c"),
    // Red only for what the cleaning throws away (DESIGN.md: "removal actions")
    error: "#de2828",
  };
}
