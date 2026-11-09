/**
 * High-contrast acoustic telemetry color lookup table (LUT) for waterfall display.
 * 256 entries x 3 channels (RGB) = 768 bytes.
 * Gradient: Deep navy/slate -> Cyan -> Emerald -> Electric Gold -> Bright White
 */
export const COLOR_LUT = new Uint8Array(256 * 3);

export function clamp(v: number): number {
  return Math.max(0, Math.min(255, Math.round(v)));
}

// Key color stops for acoustic waterfall
const STOPS = [
  { p: 0.0, r: 8, g: 14, b: 24 },     // Zero energy: deep night sky
  { p: 0.15, r: 12, g: 42, b: 77 },   // Low ambient: dark blue
  { p: 0.35, r: 14, g: 110, b: 120 }, // Normal flow: dark teal
  { p: 0.55, r: 16, g: 185, b: 129 }, // Detectable signal: emerald green
  { p: 0.75, r: 245, g: 158, b: 11 }, // Leak threshold: vibrant amber
  { p: 0.90, r: 239, g: 68, b: 68 },  // High energy / burst: crimson
  { p: 1.0, r: 254, g: 240, b: 138 }, // Peak amplitude: hot electric yellow/white
];

for (let i = 0; i < 256; i++) {
  const norm = i / 255;
  let lower = STOPS[0];
  let upper = STOPS[STOPS.length - 1];

  for (let s = 0; s < STOPS.length - 1; s++) {
    if (norm >= STOPS[s].p && norm <= STOPS[s + 1].p) {
      lower = STOPS[s];
      upper = STOPS[s + 1];
      break;
    }
  }

  const range = upper.p - lower.p;
  const t = range > 0 ? (norm - lower.p) / range : 0;
  // Smooth cubic Hermite interpolation
  const u = t * t * (3 - 2 * t);

  const idx = i * 3;
  COLOR_LUT[idx] = clamp(lower.r + (upper.r - lower.r) * u);
  COLOR_LUT[idx + 1] = clamp(lower.g + (upper.g - lower.g) * u);
  COLOR_LUT[idx + 2] = clamp(lower.b + (upper.b - lower.b) * u);
}
