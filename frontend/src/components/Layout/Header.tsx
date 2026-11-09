import { useState, useEffect } from "react";
import { Activity, Zap, PlayCircle, Sliders } from "lucide-react";
import type { Connection, Mode } from "../../hooks/useStream";

const CONN: Record<Connection, { text: string; cls: string }> = {
  connecting: { text: "Connecting...", cls: "warn" },
  waiting: { text: "Connected (Standby)", cls: "warn" },
  live: { text: "Connected (Live)", cls: "ok" },
  reconnecting: { text: "Reconnecting", cls: "bad" },
  demo: { text: "Scenario Simulation", cls: "sim" },
  "demo-paused": { text: "Simulation Paused", cls: "sim" },
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
  const [timeStr, setTimeStr] = useState<string>("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimeStr(now.toTimeString().split(" ")[0] + " UTC");
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-icon">
          <Activity size={24} />
        </div>
        <div>
          <div className="wordmark">SynthLeak</div>
          <div className="tagline">Acoustic Pipeline Leak Intelligence Platform</div>
        </div>
      </div>

      <div className="header-stats">
        <div className="stat-chip">
          <span className="stat-chip-label">Monitored Lines</span>
          <span className="stat-chip-val">4 Distribution</span>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-label">Sensors</span>
          <span className="stat-chip-val">8 Nodes @ 44.1 kHz</span>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-label">ML Core</span>
          <span className="stat-chip-val">CNN 4-Class</span>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-label">System Time</span>
          <span className="stat-chip-val">{timeStr}</span>
        </div>
      </div>

      <div className="controls">
        <div className="seg" role="group" aria-label="Data source">
          <button
            className={mode === "live" ? "on" : ""}
            aria-pressed={mode === "live"}
            onClick={() => onMode("live")}
            title="Stream real-time telemetry from FastAPI backend"
          >
            <Zap size={14} /> Live Backend
          </button>
          <button
            className={mode === "demo" ? "on" : ""}
            aria-pressed={mode === "demo"}
            onClick={() => onMode("demo")}
            title="In-browser 5-phase acoustic simulator"
          >
            <PlayCircle size={14} /> Demo Simulator
          </button>
        </div>

        <label
          className="switch"
          title="Adaptive Noise Suppression: Spectral subtraction for background urban noise filtering."
        >
          <input
            type="checkbox"
            checked={suppress}
            onChange={(e) => onSuppress(e.target.checked)}
          />
          <span className="track" aria-hidden="true">
            <span className="thumb" />
          </span>
          <span style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Sliders size={12} /> Noise Suppression
            </span>
            <small style={{ color: "var(--ink-muted)", fontSize: 11 }}>
              {!suppress ? "Off" : bgReady ? "Active (Spectral Subtraction)" : "Learning Baseline..."}
            </small>
          </span>
        </label>

        <span className={`pill ${c.cls}`} role="status">
          <i aria-hidden="true" />
          {c.text}
        </span>
      </div>
    </header>
  );
}
