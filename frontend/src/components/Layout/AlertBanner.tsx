import { AlertTriangle, CheckCircle2, Wrench, Volume2 } from "lucide-react";
import { CLASS_NAMES, SEVERITY_NAMES } from "../../lib/labels";
import { formatKHz, formatMeters, formatPercent } from "../../lib/format";
import type { AlertRecord, SpectrogramFrame } from "../../types/contract";

interface Props {
  frame: SpectrogramFrame | null;
  record: AlertRecord | null;
  onCreateTicket: (a: AlertRecord) => void;
}

export default function AlertBanner({ frame, record, onCreateTicket }: Props) {
  if (!frame) {
    return (
      <div className="banner idle" role="status">
        <Volume2 size={18} style={{ color: "var(--ink-muted)" }} />
        <span>Acoustic acquisition ready. Launch the backend or select Demo Simulator to stream acoustic data.</span>
      </div>
    );
  }

  const a = frame.alert;
  const c = frame.classification;

  if (!a.is_alert) {
    return (
      <div className="banner calm" role="status">
        <CheckCircle2 size={20} style={{ color: "var(--ok)", flexShrink: 0 }} />
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span>
            Continuous Monitoring: <strong>{frame.pipeline_id}</strong> ({frame.sensor_id}) &mdash; {CLASS_NAMES[c.class_label]}. All acoustic signals nominal.
          </span>
          {frame.is_simulated && <span className="sim-tag">Simulated Data</span>}
        </div>
      </div>
    );
  }

  return (
    <div className={`banner alarm sev-${a.severity}`} role="alert">
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <AlertTriangle
          size={28}
          style={{
            color: a.severity === "CRITICAL" ? "#ef4444" : "#f59e0b",
            flexShrink: 0,
          }}
        />
        <div className="banner-main">
          <strong>
            {SEVERITY_NAMES[a.severity]}: {CLASS_NAMES[c.class_label]} Detected on {frame.pipeline_id}
          </strong>
          <span className="banner-meta">
            Dominant Peak: <strong>{formatKHz(c.dominant_frequency_hz)} kHz</strong> &bull; Confidence: <strong>{formatPercent(c.confidence)}</strong> &bull; Estimated Location: <strong>{formatMeters(record?.estimated_chainage_meters)}</strong> along chainage
            {frame.is_simulated && <span className="sim-tag">Simulated</span>}
          </span>
        </div>
      </div>

      {record && !record.ticket_id ? (
        <button className="btn light" onClick={() => onCreateTicket(record)}>
          <Wrench size={16} /> Dispatch Work Order
        </button>
      ) : record?.ticket_id ? (
        <span className="ticketed">Work Order Active: {record.ticket_id}</span>
      ) : (
        <span style={{ fontSize: 13, color: "var(--ink-secondary)" }}>Awaiting alert record...</span>
      )}
    </div>
  );
}
