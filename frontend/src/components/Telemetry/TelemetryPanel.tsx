import { CLASS_NAMES } from "../../lib/labels";
import { formatKHz, formatPercent } from "../../lib/format";
import { FILTER_HIGH_CUT_HZ, FILTER_LOW_CUT_HZ, type SpectrogramFrame } from "../../types/contract";
import { hzToMel } from "../../lib/mel";

const DB_MIN = -90;

function LevelGauge({ db }: { db: number | null }) {
  const R = 64;
  const C = Math.PI * R; // half circle length
  const frac = db == null ? 0 : Math.min(1, Math.max(0, (db - DB_MIN) / -DB_MIN));
  const loud = db != null && db > -12;
  return (
    <div className="tile" aria-label="Sound level">
      <div className="tile-title">Sound level</div>
      <svg viewBox="0 0 160 96" className="gauge" role="img" aria-label={db == null ? "No signal" : `${db.toFixed(1)} decibels full scale`}>
        <path d="M16 84 A64 64 0 0 1 144 84" fill="none" stroke="var(--line)" strokeWidth="12" strokeLinecap="round" />
        <path d="M16 84 A64 64 0 0 1 144 84" fill="none" stroke={loud ? "var(--crit)" : "var(--teal)"} strokeWidth="12"
          strokeLinecap="round" strokeDasharray={`${C * frac} ${C}`} />
        <text x="80" y="72" textAnchor="middle" className="gauge-value">{db == null ? "--" : db.toFixed(0)}</text>
        <text x="16" y="96" textAnchor="middle" className="gauge-tick">-90</text>
        <text x="144" y="96" textAnchor="middle" className="gauge-tick">0</text>
      </svg>
      <div className="tile-sub">dBFS (RMS)</div>
    </div>
  );
}

function FrequencyTile({ hz }: { hz: number | null }) {
  const lo = hzToMel(FILTER_LOW_CUT_HZ);
  const hi = hzToMel(FILTER_HIGH_CUT_HZ);
  const pos = (f: number) => `${((hzToMel(f) - lo) / (hi - lo)) * 100}%`;
  return (
    <div className="tile" aria-label="Dominant frequency">
      <div className="tile-title">Dominant frequency</div>
      <div className="big">{hz == null ? "--" : formatKHz(hz)}<small>kHz</small></div>
      <div className="fbar" aria-hidden="true">
        <div className="fbar-band" style={{ left: pos(1500), width: `calc(${pos(8000)} - ${pos(1500)})` }} />
        {hz != null && <div className="fbar-marker" style={{ left: pos(Math.min(Math.max(hz, FILTER_LOW_CUT_HZ), FILTER_HIGH_CUT_HZ)) }} />}
      </div>
      <div className="tile-sub">Shaded: typical leak hiss band</div>
    </div>
  );
}

function ConfidenceTile({ c }: { c: number | null }) {
  return (
    <div className="tile" aria-label="Model confidence">
      <div className="tile-title">Model confidence</div>
      <div className="big">{c == null ? "--" : formatPercent(c)}</div>
      <div className="meter" aria-hidden="true"><div style={{ width: c == null ? "0%" : formatPercent(c) }} /></div>
      <div className="tile-sub">Softmax probability of the top class</div>
    </div>
  );
}

function ClassTile({ f }: { f: SpectrogramFrame | null }) {
  const sev = f?.alert.severity ?? "NONE";
  return (
    <div className={`tile class-tile sev-${sev}`} aria-label="Detected sound">
      <div className="tile-title">Detected sound</div>
      <div className="class-name">{f ? CLASS_NAMES[f.classification.class_label] : "--"}</div>
      <div className="tile-sub">{f ? f.classification.class_label : "Waiting for audio"}</div>
    </div>
  );
}

export default function TelemetryPanel({ frame }: { frame: SpectrogramFrame | null }) {
  return (
    <section className="telemetry" aria-label="Live telemetry">
      <ClassTile f={frame} />
      <ConfidenceTile c={frame?.classification.confidence ?? null} />
      <FrequencyTile hz={frame?.classification.dominant_frequency_hz ?? null} />
      <LevelGauge db={frame?.sound_level_db ?? null} />
    </section>
  );
}
