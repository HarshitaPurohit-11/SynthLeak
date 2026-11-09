import { CLASS_NAMES, SEVERITY_NAMES } from "../../lib/labels";
import { formatDateTime, formatKHz, formatMeters, formatPercent } from "../../lib/format";
import type { AlertRecord } from "../../types/contract";

interface Props {
  alerts: AlertRecord[];
  selectedId: string | null;
  onSelect: (a: AlertRecord) => void;
  onCreateTicket: (a: AlertRecord) => void;
}

const ICON: Record<string, string> = { CRITICAL: "\u25B2", WARNING: "\u25C6", INFO: "\u25CF", NONE: "\u25CB" };

export default function AlertList({ alerts, selectedId, onSelect, onCreateTicket }: Props) {
  if (alerts.length === 0) {
    return (
      <div className="empty">
        <strong>No alerts yet</strong>
        <span>When the model flags a pinhole leak or burst, it appears here with its estimated location.</span>
      </div>
    );
  }
  return (
    <ul className="alert-list">
      {alerts.map((a) => (
        <li key={a.alert_id} className={`alert-item sev-${a.severity}${a.alert_id === selectedId ? " selected" : ""}`}>
          <button className="alert-main" onClick={() => onSelect(a)} aria-pressed={a.alert_id === selectedId}>
            <span className={`badge sev-${a.severity}`}><span aria-hidden="true">{ICON[a.severity]}</span> {SEVERITY_NAMES[a.severity]}</span>
            <span className="alert-title">{CLASS_NAMES[a.class_label]} on {a.pipeline_id}</span>
            <span className="alert-meta">
              {formatDateTime(a.timestamp)} &middot; {a.sensor_id} &middot; {formatPercent(a.confidence)} confidence &middot; {formatKHz(a.dominant_frequency_hz)} kHz
            </span>
            <span className="alert-meta">Estimated position: {formatMeters(a.estimated_chainage_meters)}{a.is_simulated ? " (simulated)" : ""}</span>
          </button>
          {a.ticket_id ? (
            <span className="ticketed">Work order {a.ticket_id}</span>
          ) : (
            <button className="btn small" onClick={() => onCreateTicket(a)}>Create work order</button>
          )}
        </li>
      ))}
    </ul>
  );
}
