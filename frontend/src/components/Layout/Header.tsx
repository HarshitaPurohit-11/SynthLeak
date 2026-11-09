import type { Connection, Mode } from "../../hooks/useStream";

const CONN: Record<Connection, { text: string; cls: string }> = {
  connecting: { text: "Connecting to backend", cls: "warn" },
  waiting: { text: "Connected, waiting for audio", cls: "warn" },
  live: { text: "Live stream", cls: "ok" },
  reconnecting: { text: "Reconnecting", cls: "bad" },
  demo: { text: "Demo replay (simulated)", cls: "sim" },
  "demo-paused": { text: "Demo paused", cls: "sim" },
};

interface Props {
  mode: Mode;
  onMode: (m: Mode) => void;
  connection: Connection;
  suppress: boolean;
  onSuppress: (v: boolean) => void;
  bgReady: boolean;
}

export default function Header({ mode, onMode, connection, suppress, onSuppress, bgReady }: Props) {
  const c = CONN[connection];
  return (
    <header className="topbar">
      <div className="brand">
        <span className="wordmark">SynthLeak</span>
        <span className="tagline">Acoustic leak monitoring for gas and water networks</span>
      </div>
      <div className="controls">
        <div className="seg" role="group" aria-label="Data source">
          <button className={mode === "live" ? "on" : ""} aria-pressed={mode === "live"} onClick={() => onMode("live")}>Live backend</button>
          <button className={mode === "demo" ? "on" : ""} aria-pressed={mode === "demo"} onClick={() => onMode("demo")}>Demo replay</button>
        </div>
        <label className="switch" title="Display-side only: subtracts the learned background from the spectrogram view. It does not change what the model hears.">
          <input type="checkbox" checked={suppress} onChange={(e) => onSuppress(e.target.checked)} />
          <span className="track" aria-hidden="true"><span className="thumb" /></span>
          <span>
            Adaptive Noise Suppression
            <small>{!suppress ? "Off" : bgReady ? "On (spectrogram view)" : "Learning background..."}</small>
          </span>
        </label>
        <span className={`pill ${c.cls}`} role="status"><i aria-hidden="true" />{c.text}</span>
      </div>
    </header>
  );
}
