import { Gauge, Radio, Target, Layers } from "lucide-react";
import { CLASS_NAMES } from "../../lib/labels";
import { formatKHz, formatPercent } from "../../lib/format";
import { FILTER_HIGH_CUT_HZ, FILTER_LOW_CUT_HZ, type SpectrogramFrame } from "../../types/contract";
import { hzToMel } from "../../lib/mel";

const DB_MIN = -90;

function LevelGauge({ db }: { db: number | null }) {
  const R = 60;
  const C = Math.PI * R; // Half circle arc length
  const frac = db == null ? 0 : Math.min(1, Math.max(0, (db - DB_MIN) / -DB_MIN));
  const loud = db != null && db > -15;

  return (
    <div className="tile" aria-label="Acoustic sound level">
      <div className="tile-title">
        <Gauge size={14} /> Sound Pressure Level
      </div>
      <svg viewBox="0 0 160 85" className="gauge" role="img" aria-label={db == null ? "No signal" : `${db.toFixed(1)} dBFS RMS`}>
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="70%" stopColor="#10b981" />
            <stop offset="90%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        <path d="M16 75 A60 60 0 0 1 144 75" fill="none" stroke="var(--bg-base)" strokeWidth="12" strokeLinecap="round" />
        <path
          d="M16 75 A60 60 0 0 1 144 75"
          fill="none"
          stroke={loud ? "var(--crit)" : "url(#gaugeGradient)"}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${C * frac} ${C}`}
          style={{ transition: "stroke-dasharray 0.15s ease" }}
        />
        <text x="80" y="65" textAnchor="middle" className="gauge-value">
          {db == null ? "--" : db.toFixed(0)}
        </text>
        <text x="18" y="84" textAnchor="middle" className="gauge-tick">-90</text>
        <text x="142" y="84" textAnchor="middle" className="gauge-tick">0</text>
      </svg>
      <div className="tile-sub">dBFS RMS (44.1 kHz window)</div>
    </div>
  );
}

function FrequencyTile({ hz }: { hz: number | null }) {
  const lo = hzToMel(FILTER_LOW_CUT_HZ);
  const hi = hzToMel(FILTER_HIGH_CUT_HZ);
  const pos = (f: number) => `${((hzToMel(f) - lo) / (hi - lo)) * 100}%`;

  return (
    <div className="tile" aria-label="Dominant spectral peak frequency">
      <div className="tile-title">
        <Radio size={14} /> Peak Spectral Frequency
      </div>
      <div className="big">
        {hz == null ? "--" : formatKHz(hz)}
        <small>kHz</small>
      </div>
      <div className="fbar" aria-hidden="true">
        <div className="fbar-band" style={{ left: pos(1500), width: `calc(${pos(8000)} - ${pos(1500)})` }} />
        {hz != null && (
          <div
            className="fbar-marker"
            style={{
              left: pos(Math.min(Math.max(hz, FILTER_LOW_CUT_HZ), FILTER_HIGH_CUT_HZ)),
            }}
          />
        )}
      </div>
      <div className="tile-sub">Gold marker in 1.5 - 8 kHz leak hiss zone</div>
    </div>
  );
}

function ConfidenceTile({ c }: { c: number | null }) {
  return (
    <div className="tile" aria-label="Model inference confidence probability">
      <div className="tile-title">
        <Target size={14} /> Model Confidence
      </div>
      <div className="big">{c == null ? "--" : formatPercent(c)}</div>
      <div className="meter" aria-hidden="true">
        <div style={{ width: c == null ? "0%" : formatPercent(c) }} />
      </div>
      <div className="tile-sub">Softmax probability of CNN prediction</div>
    </div>
  );
}

function ClassTile({ f }: { f: SpectrogramFrame | null }) {
  const sev = f?.alert.severity ?? "NONE";
  return (
    <div className={`tile class-tile sev-${sev}`} aria-label="Detected acoustic classification">
      <div className="tile-title">
        <Layers size={14} /> Acoustic Signature
      </div>
      <div className="class-name">{f ? CLASS_NAMES[f.classification.class_label] : "Acquiring..."}</div>
      <div className="tile-sub">
        {f ? (
          <span>Raw Category: <code>{f.classification.class_label}</code></span>
        ) : (
          "Listening for audio emission..."
        )}
      </div>
    </div>
  );
}

export default function TelemetryPanel({ frame }: { frame: SpectrogramFrame | null }) {
  return (
    <section className="telemetry" aria-label="Real-time acoustic telemetry">
      <ClassTile f={frame} />
      <ConfidenceTile c={frame?.classification.confidence ?? null} />
      <FrequencyTile hz={frame?.classification.dominant_frequency_hz ?? null} />
      <LevelGauge db={frame?.sound_level_db ?? null} />
    </section>
  );
}
