import type { DemoControls } from "../../hooks/useStream";

export default function DemoBar({ demo }: { demo: DemoControls }) {
  return (
    <section className="demobar" aria-label="Demo replay controls">
      <div className="demo-buttons">
        <button className="btn small" onClick={demo.toggle}>{demo.playing ? "Pause" : "Play"}</button>
        <button className="btn small ghost" onClick={demo.restart}>Restart</button>
      </div>
      <div className="timeline" aria-hidden="true">
        {demo.phases.map((p) => (
          <div key={p.id} className={`seg-phase ${p.id}${p.id === demo.phase.id ? " now" : ""}`} style={{ flex: p.duration }}>
            <span>{p.label}</span>
          </div>
        ))}
        <div className="playhead" style={{ left: `${(demo.elapsed / demo.total) * 100}%` }} />
      </div>
      <div className="demo-note"><strong>Simulated scenario.</strong> {demo.phase.note}.</div>
    </section>
  );
}
