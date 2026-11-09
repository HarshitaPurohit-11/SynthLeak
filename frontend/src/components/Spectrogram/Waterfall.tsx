import { useEffect, useMemo, useRef } from "react";
import { COLOR_LUT } from "../../lib/colormap";
import { hzToMelBin } from "../../lib/mel";
import { N_MELS, type SpectrogramFrame } from "../../types/contract";

const HISTORY = 480; // columns kept on screen (~32 s at 15 fps)
const AXIS_HZ = [200, 500, 1000, 2000, 4000, 8000];
const LEAK_LO = 1500;
const LEAK_HI = 8000;
const EMA = 0.97;
const MIN_BG_FRAMES = 20;
const SUPPRESS_GAIN = 1.15;

interface Props {
  subscribe: (cb: (f: SpectrogramFrame) => void) => () => void;
  suppress: boolean;
  hasSource: boolean;
  emptyTitle: string;
  emptyHint: string;
  onBackgroundReady: (ready: boolean) => void;
}

function rowPercent(hz: number): number {
  return ((N_MELS - 1 - hzToMelBin(hz) + 0.5) / N_MELS) * 100;
}

/** Scrolling waterfall: newest frame is drawn at the right edge, history moves left. */
export default function Waterfall({ subscribe, suppress, hasSource, emptyTitle, emptyHint, onBackgroundReady }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const suppressRef = useRef(suppress);
  const profile = useRef<Float32Array>(new Float32Array(N_MELS));
  const bgFrames = useRef(0);
  const readyRef = useRef(false);
  const hasDrawn = useRef(false);
  const emptyRef = useRef<HTMLDivElement>(null);
  suppressRef.current = suppress;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { willReadFrequently: false });
    if (!ctx) return;
    ctx.fillStyle = `rgb(${COLOR_LUT[0]}, ${COLOR_LUT[1]}, ${COLOR_LUT[2]})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const column = ctx.createImageData(1, N_MELS);
    hasDrawn.current = false;
    bgFrames.current = 0;
    readyRef.current = false;
    profile.current.fill(0);
    onBackgroundReady(false);

    const unsub = subscribe((f) => {
      const bins = f.spectrogram_frame;
      // Learn the background from frames the model labelled NORMAL_FLOW / AMBIENT_URBAN.
      if (f.classification.class_id <= 1) {
        const p = profile.current;
        for (let i = 0; i < N_MELS; i++) p[i] = bgFrames.current === 0 ? bins[i] : EMA * p[i] + (1 - EMA) * bins[i];
        bgFrames.current += 1;
        if (!readyRef.current && bgFrames.current >= MIN_BG_FRAMES) {
          readyRef.current = true;
          onBackgroundReady(true);
        }
      }
      const doSuppress = suppressRef.current && readyRef.current;
      ctx.drawImage(canvas, -1, 0);
      for (let bin = 0; bin < N_MELS; bin++) {
        let v = bins[bin];
        if (doSuppress) v = (v - SUPPRESS_GAIN * profile.current[bin]) * 1.3;
        const idx = Math.round(Math.min(1, Math.max(0, v)) * 255) * 3;
        const o = (N_MELS - 1 - bin) * 4;
        column.data[o] = COLOR_LUT[idx];
        column.data[o + 1] = COLOR_LUT[idx + 1];
        column.data[o + 2] = COLOR_LUT[idx + 2];
        column.data[o + 3] = 255;
      }
      ctx.putImageData(column, canvas.width - 1, 0);
      if (!hasDrawn.current) {
        hasDrawn.current = true;
        if (emptyRef.current) emptyRef.current.style.display = "none";
      }
    });
    return unsub;
  }, [subscribe, onBackgroundReady]);

  // Show the empty state again when the source is lost / switched.
  useEffect(() => {
    if (!hasSource && emptyRef.current) emptyRef.current.style.display = "";
  }, [hasSource]);

  const ticks = useMemo(
    () => AXIS_HZ.map((hz) => ({ hz, top: rowPercent(hz), label: hz >= 1000 ? `${hz / 1000} kHz` : `${hz} Hz` })),
    [],
  );
  const bandTop = rowPercent(LEAK_HI);
  const bandBottom = rowPercent(LEAK_LO);

  return (
    <div className="wf">
      <canvas ref={canvasRef} width={HISTORY} height={N_MELS} className="wf-canvas"
        role="img" aria-label="Live waterfall spectrogram. Frequency runs bottom to top, time runs left to right." />
      <div className="wf-axis" aria-hidden="true">
        {ticks.map((t) => (
          <span key={t.hz} style={{ top: `${t.top}%` }}>{t.label}</span>
        ))}
      </div>
      <div className="wf-band" aria-hidden="true" style={{ top: `${bandTop}%`, height: `${bandBottom - bandTop}%` }}>
        <span>Leak hiss band</span>
      </div>
      <div className="wf-now" aria-hidden="true">now</div>
      <div ref={emptyRef} className="wf-empty" role="status">
        <strong>{emptyTitle}</strong>
        <span>{emptyHint}</span>
      </div>
    </div>
  );
}
