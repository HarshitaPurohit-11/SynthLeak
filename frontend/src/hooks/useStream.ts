import { useCallback, useEffect, useRef, useState } from "react";
import { DEMO_PIPELINES } from "../demo/fixtures";
import {
  PHASES, PHASE_PIPE_STATUS, SCENARIO_SECONDS, demoAlertFor, phaseAt, synthFrame, toContractFrame,
  type Phase,
} from "../demo/scenario";
import { wsUrl } from "../services/api";
import { WsClient, type WsStatus } from "../services/ws";
import { WS_TARGET_FPS, type AlertRecord, type PipelineStatus, type SpectrogramFrame } from "../types/contract";

export type Mode = "live" | "demo";
export type Connection = "connecting" | "waiting" | "live" | "reconnecting" | "demo" | "demo-paused";

export interface DemoControls {
  playing: boolean;
  toggle: () => void;
  restart: () => void;
  elapsed: number;
  total: number;
  phase: Phase;
  phases: Phase[];
  alerts: AlertRecord[];
  pipelineStatus: Record<string, PipelineStatus>;
  resetCount: number;
}

export interface StreamApi {
  connection: Connection;
  latest: SpectrogramFrame | null;
  /** Subscribe to every frame (used by the canvas, which must not re-render React per frame). */
  subscribe: (cb: (f: SpectrogramFrame) => void) => () => void;
  demo: DemoControls | null;
  failedAttempts: number;
}

const UI_THROTTLE_MS = 150;

export function useStream(mode: Mode): StreamApi {
  const subs = useRef(new Set<(f: SpectrogramFrame) => void>());
  const lastUi = useRef(0);
  const lastKey = useRef("");
  const [latest, setLatest] = useState<SpectrogramFrame | null>(null);
  const [wsStatus, setWsStatus] = useState<WsStatus>("connecting");
  const [gotFrame, setGotFrame] = useState(false);
  const [failedAttempts, setFailedAttempts] = useState(0);

  // demo state
  const [playing, setPlaying] = useState(true);
  const [elapsed, setElapsed] = useState(0);
  const [demoAlerts, setDemoAlerts] = useState<AlertRecord[]>([]);
  const [resetCount, setResetCount] = useState(0);
  const [phase, setPhase] = useState<Phase>(PHASES[0]);
  const tRef = useRef(0);
  const idxRef = useRef(0);
  const phaseRef = useRef<string>("");
  const playingRef = useRef(true);
  playingRef.current = playing;

  const subscribe = useCallback((cb: (f: SpectrogramFrame) => void) => {
    subs.current.add(cb);
    return () => { subs.current.delete(cb); };
  }, []);

  const emit = useCallback((f: SpectrogramFrame) => {
    subs.current.forEach((cb) => cb(f));
    const key = `${f.classification.class_id}|${f.alert.is_alert}|${f.pipeline_id}`;
    const now = performance.now();
    if (key !== lastKey.current || now - lastUi.current > UI_THROTTLE_MS) {
      lastKey.current = key;
      lastUi.current = now;
      setLatest(f);
    }
  }, []);

  // ---- live WebSocket -----------------------------------------------------------------
  useEffect(() => {
    if (mode !== "live") return;
    setLatest(null);
    setGotFrame(false);
    setFailedAttempts(0);
    lastKey.current = "";
    const client = new WsClient(wsUrl(), {
      onFrame: (f) => { setGotFrame(true); emit(f); },
      onStatus: (s) => {
        setWsStatus(s);
        if (s === "reconnecting") setFailedAttempts((n) => n + 1);
        if (s === "open") setFailedAttempts(0);
      },
    });
    client.start();
    return () => client.stop();
  }, [mode, emit]);

  // ---- demo replay ----------------------------------------------------------------------
  useEffect(() => {
    if (mode !== "demo") return;
    setLatest(null);
    lastKey.current = "";
    let last = performance.now();
    const id = window.setInterval(() => {
      const now = performance.now();
      const dt = (now - last) / 1000;
      last = now;
      if (!playingRef.current) return;
      tRef.current += dt;
      idxRef.current += 1;
      const t = tRef.current;
      const synth = synthFrame(t, idxRef.current);
      const nowIso = new Date().toISOString();
      const frame = toContractFrame(synth, nowIso);
      if (synth.phase.id !== phaseRef.current) {
        phaseRef.current = synth.phase.id;
        setPhase(synth.phase);
        if (synth.phase.id === "leak" || synth.phase.id === "burst") {
          const loop = Math.floor(t / SCENARIO_SECONDS);
          setDemoAlerts((prev) => [demoAlertFor(synth.phase.id as "leak" | "burst", loop, nowIso, frame), ...prev]);
        }
      }
      emit(frame);
      if (idxRef.current % 5 === 0) setElapsed(t % SCENARIO_SECONDS);
    }, Math.round(1000 / WS_TARGET_FPS));
    return () => window.clearInterval(id);
  }, [mode, emit]);

  const restart = useCallback(() => {
    tRef.current = 0;
    idxRef.current = 0;
    phaseRef.current = "";
    setElapsed(0);
    setDemoAlerts([]);
    setPhase(PHASES[0]);
    setPlaying(true);
    setResetCount((n) => n + 1);
  }, []);
  const toggle = useCallback(() => setPlaying((p) => !p), []);

  const current = phaseAt(elapsed);
  const pipelineStatus: Record<string, PipelineStatus> = {};
  for (const p of DEMO_PIPELINES) pipelineStatus[p.pipeline_id] = "NORMAL";
  pipelineStatus["PIPE-001"] = PHASE_PIPE_STATUS[phase.id];

  let connection: Connection;
  if (mode === "demo") connection = playing ? "demo" : "demo-paused";
  else if (wsStatus === "open") connection = gotFrame ? "live" : "waiting";
  else connection = wsStatus;

  const demo: DemoControls | null = mode === "demo"
    ? { playing, toggle, restart, elapsed, total: SCENARIO_SECONDS, phase: current.id === phase.id ? phase : current,
        phases: PHASES, alerts: demoAlerts, pipelineStatus, resetCount }
    : null;

  return { connection, latest, subscribe, demo, failedAttempts };
}
