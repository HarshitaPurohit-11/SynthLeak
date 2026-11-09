// Scripted, looping demo scenario. The frames are SYNTHESISED in the browser (clearly labelled
// "Simulated" in the UI): traffic baseline -> quiet flow -> pinhole leak -> burst -> repaired.
// Class, dominant frequency and sound level are derived from the synthesised frame itself,
// not typed in as fixed numbers. Confidence is a simulated value and is flagged as such.
import type {
  AlertRecord, ClassId, PipelineStatus, SpectrogramFrame, Severity,
} from "../types/contract";
import { CLASS_LABELS, N_MELS } from "../types/contract";
import { melBinCenterHz } from "../lib/mel";

export interface Phase {
  id: "baseline" | "normal" | "leak" | "burst" | "recover";
  label: string;
  note: string;
  start: number;
  duration: number;
  classId: ClassId;
}

const RAW: Omit<Phase, "start">[] = [
  { id: "baseline", label: "Traffic baseline", note: "Street noise only, no leak", duration: 9, classId: 1 },
  { id: "normal", label: "Quiet flow", note: "Normal water flow", duration: 5, classId: 0 },
  { id: "leak", label: "Pinhole leak starts", note: "Steady hiss appears at 1.5-8 kHz", duration: 14, classId: 2 },
  { id: "burst", label: "Pressure transient", note: "Cavitation / burst events", duration: 7, classId: 3 },
  { id: "recover", label: "Repair complete", note: "Back to normal flow", duration: 6, classId: 0 },
];

export const PHASES: Phase[] = (() => {
  let t = 0;
  return RAW.map((p) => {
    const ph = { ...p, start: t };
    t += p.duration;
    return ph;
  });
})();

export const SCENARIO_SECONDS = PHASES.reduce((a, p) => a + p.duration, 0);

export function phaseAt(t: number): Phase {
  const tt = ((t % SCENARIO_SECONDS) + SCENARIO_SECONDS) % SCENARIO_SECONDS;
  return PHASES.find((p) => tt >= p.start && tt < p.start + p.duration) ?? PHASES[0];
}

/** Pipeline PIPE-001 status for each phase (the other fixture pipelines stay NORMAL). */
export const PHASE_PIPE_STATUS: Record<Phase["id"], PipelineStatus> = {
  baseline: "NORMAL", normal: "NORMAL", leak: "WARNING", burst: "CRITICAL", recover: "NORMAL",
};

// Small seeded PRNG so a given frame index always renders the same noise (testable, repeatable).
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const smooth = (x: number, a: number, b: number) => {
  const u = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return u * u * (3 - 2 * u);
};
const BIN_HZ = Array.from({ length: N_MELS }, (_, i) => melBinCenterHz(i));

interface Mix { traffic: number; flow: number; leak: number; burst: number }
const MIX: Record<Phase["id"], Mix> = {
  baseline: { traffic: 0.62, flow: 0.12, leak: 0, burst: 0 },
  normal: { traffic: 0.1, flow: 0.28, leak: 0, burst: 0 },
  leak: { traffic: 0.34, flow: 0.12, leak: 1, burst: 0 },
  burst: { traffic: 0.3, flow: 0.12, leak: 0.35, burst: 1 },
  recover: { traffic: 0.08, flow: 0.26, leak: 0, burst: 0 },
};

export interface SynthFrame {
  bins: number[];
  classId: ClassId;
  confidence: number;
  dominantHz: number;
  levelDb: number;
  phase: Phase;
}

/** Synthesise the Mel column at scenario time ``t`` (seconds). ``index`` seeds the noise. */
export function synthFrame(t: number, index: number): SynthFrame {
  const phase = phaseAt(t);
  const local = (((t % SCENARIO_SECONDS) + SCENARIO_SECONDS) % SCENARIO_SECONDS) - phase.start;
  const rnd = mulberry32(index * 2654435761);
  const mix = MIX[phase.id];
  const fade = smooth(local, 0, 0.8); // ease into each phase so the waterfall does not jump
  const swell = 0.75 + 0.25 * Math.sin(2 * Math.PI * 0.35 * t);
  const peakHz = 4200 + 450 * Math.sin(2 * Math.PI * 0.07 * t);
  // Burst events: a few decaying broadband impulses per second.
  const eventPhase = (t * 2.3) % 1;
  const burstEnv = mix.burst * Math.exp(-eventPhase * 5) * (0.6 + 0.4 * rnd());

  const bins = BIN_HZ.map((f) => {
    const traffic = mix.traffic * swell * Math.exp(-Math.pow(f / 750, 1.5));
    const flow = mix.flow * Math.exp(-Math.pow(f / 420, 1.2));
    const band = smooth(f, 1500, 2200) * (1 - smooth(f, 6500, 8800));
    const bump = Math.exp(-0.5 * Math.pow((f - peakHz) / 750, 2));
    const leak = mix.leak * (0.34 * band + 0.38 * bump * band);
    const burst = burstEnv * (0.9 * smooth(f, 200, 600) * (1 - smooth(f, 8000, 10000)) + 0.4 * Math.exp(-f / 300));
    const noise = 0.035 * rnd();
    return Math.min(1, Math.max(0, (traffic + flow + leak + burst) * (0.85 + 0.15 * fade) + noise));
  });

  // Derive dominant frequency and level from the frame itself.
  const sm = bins.map((_, i) => {
    let s = 0, n = 0;
    for (let k = -2; k <= 2; k++) if (bins[i + k] !== undefined) { s += bins[i + k]; n++; }
    return s / n;
  });
  let best = 0;
  sm.forEach((v, i) => { if (v > sm[best]) best = i; });
  const mean = bins.reduce((a, b) => a + b, 0) / N_MELS;
  const levelDb = Math.max(-90, Math.min(0, -62 + 80 * mean + 2 * (rnd() - 0.5)));
  const confidence = Math.min(0.99, Math.max(0.5, 0.88 + 0.07 * Math.sin(t * 1.3) + 0.03 * (rnd() - 0.5)));
  return { bins, classId: phase.classId, confidence, dominantHz: BIN_HZ[best], levelDb, phase };
}

const SEVERITY_BY_CLASS: Record<ClassId, Severity> = { 0: "NONE", 1: "INFO", 2: "WARNING", 3: "CRITICAL" };
const MESSAGE_BY_CLASS: Record<ClassId, string> = {
  0: "Normal flow",
  1: "Urban noise detected - no action needed",
  2: "Acoustic anomaly: High-frequency pinhole leak signature",
  3: "Acoustic anomaly: Transient burst / cavitation signature",
};

export const DEMO_PIPELINE_ID = "PIPE-001";
export const DEMO_SENSOR_ID = "SENSOR-A1";

export function toContractFrame(s: SynthFrame, nowIso: string): SpectrogramFrame {
  const isAlert = s.classId >= 2;
  return {
    message_type: "spectrogram_frame",
    timestamp: nowIso,
    pipeline_id: DEMO_PIPELINE_ID,
    sensor_id: DEMO_SENSOR_ID,
    spectrogram_frame: s.bins.map((v) => Math.round(v * 1000) / 1000),
    classification: {
      class_id: s.classId,
      class_label: CLASS_LABELS[s.classId],
      confidence: Math.round(s.confidence * 10000) / 10000,
      dominant_frequency_hz: Math.round(s.dominantHz * 10) / 10,
    },
    sound_level_db: Math.round(s.levelDb * 10) / 10,
    alert: {
      is_alert: isAlert,
      severity: SEVERITY_BY_CLASS[s.classId],
      message: `${MESSAGE_BY_CLASS[s.classId]}${isAlert ? ` on ${DEMO_PIPELINE_ID}` : ""}`,
    },
    is_simulated: true,
  };
}

/** Alert records "raised" by the scenario, with the loop number so each cycle gets fresh ids. */
export function demoAlertFor(phaseId: "leak" | "burst", loop: number, nowIso: string, frame: SpectrogramFrame): AlertRecord {
  const n = loop * 2 + (phaseId === "leak" ? 1 : 2);
  return {
    alert_id: `SIM-ALT-${String(n).padStart(4, "0")}`,
    pipeline_id: DEMO_PIPELINE_ID,
    sensor_id: DEMO_SENSOR_ID,
    timestamp: nowIso,
    class_id: frame.classification.class_id,
    class_label: frame.classification.class_label,
    confidence: frame.classification.confidence,
    dominant_frequency_hz: frame.classification.dominant_frequency_hz,
    sound_level_db: frame.sound_level_db,
    severity: frame.alert.severity,
    // Simulated localisation (the real system derives this from two-sensor cross-correlation).
    estimated_chainage_meters: phaseId === "leak" ? 412.5 : 655.0,
    is_acknowledged: false,
    ticket_id: null,
    is_simulated: true,
  };
}
