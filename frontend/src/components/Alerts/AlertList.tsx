import { useState } from "react";
import { AlertCircle, MapPin, Calendar, Wrench, Search, CheckCircle } from "lucide-react";
import { CLASS_NAMES, SEVERITY_NAMES } from "../../lib/labels";
import { formatDateTime, formatKHz, formatMeters, formatPercent } from "../../lib/format";
import type { AlertRecord } from "../../types/contract";

interface Props {
  alerts: AlertRecord[];
  selectedId: string | null;
  onSelect: (a: AlertRecord) => void;
  onCreateTicket: (a: AlertRecord) => void;
}

export default function AlertList({ alerts, selectedId, onSelect, onCreateTicket }: Props) {
  const [query, setQuery] = useState("");
  const [filterSev, setFilterSev] = useState<string>("ALL");

  const filtered = alerts.filter((a) => {
    const matchesQuery =
      a.pipeline_id.toLowerCase().includes(query.toLowerCase()) ||
      a.sensor_id.toLowerCase().includes(query.toLowerCase()) ||
      CLASS_NAMES[a.class_label].toLowerCase().includes(query.toLowerCase());
    const matchesSev = filterSev === "ALL" || a.severity === filterSev;
    return matchesQuery && matchesSev;
  });

  if (alerts.length === 0) {
    return (
      <div className="empty">
        <CheckCircle size={32} style={{ color: "var(--ok)", margin: "0 auto" }} />
        <strong>No Active Acoustic Anomalies</strong>
        <span>Continuous baseline monitoring in progress. Any pinhole leaks or bursts will appear here automatically.</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", gap: 8, padding: "0 2px" }}>
        <div style={{ position: "relative", flex: 1 }}>
          <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--ink-muted)" }} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search alerts by pipe, sensor, or type..."
            style={{
              width: "100%",
              padding: "6px 10px 6px 30px",
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              color: "#ffffff",
              fontSize: "12px",
              outline: "none",
            }}
          />
        </div>
        <select
          value={filterSev}
          onChange={(e) => setFilterSev(e.target.value)}
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "6px",
            color: "var(--ink-secondary)",
            fontSize: "12px",
            padding: "0 8px",
            outline: "none",
          }}
        >
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="WARNING">Warning</option>
          <option value="INFO">Info</option>
        </select>
      </div>

      <ul className="alert-list">
        {filtered.map((a) => (
          <li
            key={a.alert_id}
            className={`alert-item sev-${a.severity}${a.alert_id === selectedId ? " selected" : ""}`}
          >
            <button
              className="alert-main"
              onClick={() => onSelect(a)}
              aria-pressed={a.alert_id === selectedId}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
                <span className={`badge sev-${a.severity}`}>
                  <AlertCircle size={12} /> {SEVERITY_NAMES[a.severity]}
                </span>
                <span style={{ fontSize: 11, color: "var(--ink-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                  <Calendar size={11} /> {formatDateTime(a.timestamp)}
                </span>
              </div>

              <span className="alert-title">
                {CLASS_NAMES[a.class_label]} on {a.pipeline_id}
              </span>

              <span className="alert-meta">
                Sensor: <code>{a.sensor_id}</code> &bull; Confidence: {formatPercent(a.confidence)} &bull; Peak: {formatKHz(a.dominant_frequency_hz)} kHz
              </span>

              <span className="alert-meta" style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--teal-accent)" }}>
                <MapPin size={12} /> Chainage: {formatMeters(a.estimated_chainage_meters)}
                {a.is_simulated && <span className="sim-tag" style={{ marginLeft: 6 }}>Simulated</span>}
              </span>
            </button>

            {a.ticket_id ? (
              <span className="ticketed">WO: {a.ticket_id}</span>
            ) : (
              <button
                className="btn small"
                onClick={(e) => {
                  e.stopPropagation();
                  onCreateTicket(a);
                }}
                title="Dispatch work order for field maintenance crew"
              >
                <Wrench size={12} /> Dispatch
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
