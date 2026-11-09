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
    return <div className="banner idle" role="status">No audio yet. Start the backend, or switch to Demo replay to see the full flow.</div>;
  }
  const a = frame.alert;
  const c = frame.classification;
  if (!a.is_alert) {
    return (
      <div className="banner calm" role="status">
        <span className="dot-ok" aria-hidden="true" />
        Monitoring {frame.pipeline_id} ({frame.sensor_id}): {CLASS_NAMES[c.class_label]}. No leak detected.
        {frame.is_simulated && <span className="sim-tag">Simulated</span>}
      </div>
    );
  }
  return (
    <div className={`banner alarm sev-${a.severity}`} role="alert">
      <div className="banner-main">
        <strong>{SEVERITY_NAMES[a.severity]}: {CLASS_NAMES[c.class_label]} on {frame.pipeline_id}</strong>
        <span>
          Peak {formatKHz(c.dominant_frequency_hz)} kHz &middot; Confidence {formatPercent(c.confidence)} &middot; Estimated position {formatMeters(record?.estimated_chainage_meters)}
          {frame.is_simulated && <span className="sim-tag">Simulated</span>}
        </span>
      </div>
      {record && !record.ticket_id ? (
        <button className="btn light" onClick={() => onCreateTicket(record)}>Create work order</button>
      ) : record?.ticket_id ? (
        <span className="ticketed on-dark">Work order {record.ticket_id}</span>
      ) : (
        <span className="hint-light">Waiting for the alert record...</span>
      )}
    </div>
  );
}
