// Text drawn on a canvas and used as a texture: the MIMIT sign, the JSON plate,
// the price sign of the petrol station. Drawn with the site's font, Jost.
import { CanvasTexture, SRGBColorSpace } from "three";

const FONT = '"Jost", "Avenir Next", system-ui, sans-serif';

function texture(width, height, draw) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  draw(canvas.getContext("2d"), width, height);
  const result = new CanvasTexture(canvas);
  result.colorSpace = SRGBColorSpace;
  result.anisotropy = 4;
  return result;
}

/** A plate with one word, centred. */
export function plateTexture(text, { background, color, width = 512, height = 128 }) {
  return texture(width, height, (ctx, w, h) => {
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = color;
    ctx.font = `700 ${Math.round(h * 0.56)}px ${FONT}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, w / 2, h / 2 + h * 0.03);
  });
}

/** "1.929" → ["1,92", "9"]: like on real price signs, the third decimal is smaller. */
export function priceParts(price) {
  const text = price.toFixed(3).replace(".", ",");
  return [text.slice(0, -1), text.slice(-1)];
}

/**
 * The price sign: a green header, then each fuel with its lowest price, then the date.
 * `draw(prices)` paints it again (the numbers count up when the scene starts).
 */
export function createPriceSign({ date, colors }) {
  let painter;
  const result = texture(320, 640, (ctx, w, h) => {
    painter = (prices) => paintPriceSign(ctx, w, h, { prices, date, colors });
  });
  return {
    texture: result,
    draw(prices) {
      painter(prices);
      result.needsUpdate = true;
    },
  };
}

function paintPriceSign(ctx, w, h, { prices, date, colors }) {
  ctx.fillStyle = colors.white;
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = colors.primary;
  ctx.fillRect(0, 0, w, 96);
  ctx.fillStyle = colors.white;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.font = `600 30px ${FONT}`;
  ctx.fillText("PIÙ ECONOMICI", w / 2, 50);

  let y = 150;
  for (const [label, price] of prices) {
    ctx.textAlign = "left";
    ctx.fillStyle = colors.body;
    ctx.font = `500 30px ${FONT}`;
    ctx.fillText(label, 28, y);

    const [main, last] = priceParts(price);
    ctx.fillStyle = colors.ink;
    ctx.font = `700 96px ${FONT}`;
    ctx.fillText(main, 24, y + 82);
    const mainWidth = ctx.measureText(main).width;
    ctx.font = `700 52px ${FONT}`;
    ctx.fillText(last, 28 + mainWidth, y + 62);

    y += 200;
  }

  ctx.textAlign = "center";
  ctx.fillStyle = colors.muted;
  ctx.font = `500 26px ${FONT}`;
  ctx.fillText(date, w / 2, h - 36);
}
