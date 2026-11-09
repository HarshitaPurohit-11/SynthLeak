export const COLOR_LUT = new Uint8Array(256 * 3);

function clamp(v: number): number {
  return Math.max(0, Math.min(255, Math.round(v)));
}

// Generate Turbo-style colormap for spectrogram waterfall
(function initLut() {
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    let r = 0, g = 0, b = 0;
    if (t < 0.25) {
      const f = t / 0.25;
      r = 15 + f * 10;
      g = 20 + f * 40;
      b = 40 + f * 160;
    } else if (t < 0.5) {
      const f = (t - 0.25) / 0.25;
      r = 25 + f * 10;
      g = 60 + f * 130;
      b = 200 - f * 40;
    } else if (t < 0.75) {
      const f = (t - 0.5) / 0.25;
      r = 35 + f * 200;
      g = 190 + f * 45;
      b = 160 - f * 140;
    } else {
      const f = (t - 0.75) / 0.25;
      r = 235 + f * 20;
      g = 235 - f * 175;
      b = 20 - f * 10;
    }
    COLOR_LUT[i * 3] = clamp(r);
    COLOR_LUT[i * 3 + 1] = clamp(g);
    COLOR_LUT[i * 3 + 2] = clamp(b);
  }
})();

