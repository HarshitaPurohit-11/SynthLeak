import { Play, Pause, RotateCcw, Info } from "lucide-react";
import type { DemoControls } from "../../hooks/useStream";

export default function DemoBar({ demo }: { demo: DemoControls }) {
  const pct = Math.min(100, Math.max(0, (demo.elapsed / demo.total) * 100));

  return (
    <div className="demobar" role="region" aria-label="Demo replay simulator controls">
      <div className="demo-buttons">
        <button
          className="btn small ghost"
          onClick={demo.toggle}
          aria-label={demo.playing ? "Pause simulation" : "Resume simulation"}
          title={demo.playing ? "Pause" : "Play"}
        >
          {demo.playing ? <Pause size={14} /> : <Play size={14} />}
          <span>{demo.playing ? "Pause" : "Resume"}</span>
        </button>
        <button
          className="btn small ghost"
          onClick={demo.restart}
          aria-label="Restart simulation cycle"
          title="Restart"
        >
          <RotateCcw size={14} />
          <span>Restart</span>
        </button>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-secondary)", marginLeft: 6 }}>
          {demo.elapsed.toFixed(1)}s / {demo.total.toFixed(0)}s
        </span>
      </div>

      <div className="timeline" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
        {demo.phases.map((p) => {
          const w = (p.duration / demo.total) * 100;
          const isNow = p.id === demo.phase.id;
          const cls = `seg-phase ${p.id}${isNow ? " now" : ""}`;
          return (
            <div key={p.id} className={cls} style={{ width: `${w}%` }} title={`${p.label}: ${p.note}`}>
              <span>{p.label}</span>
            </div>
          );
        })}
        <div className="playhead" style={{ left: `${pct}%` }} />
      </div>

      <div className="demo-note">
        <Info size={16} style={{ flexShrink: 0 }} />
        <span><strong>{demo.phase.label}:</strong> {demo.phase.note}</span>
      </div>
    </div>
  );
}
