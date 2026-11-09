import { ClipboardList, Clock, User, MapPin } from "lucide-react";
import { formatDateTime, formatMeters } from "../../lib/format";
import type { Ticket } from "../../types/contract";

export default function TicketList({ tickets }: { tickets: Ticket[] }) {
  if (tickets.length === 0) {
    return (
      <div className="empty">
        <ClipboardList size={32} style={{ color: "var(--ink-muted)", margin: "0 auto" }} />
        <strong>No Work Orders Dispatched</strong>
        <span>Select an acoustic leak alert and click Dispatch to send a repair crew to the pinpointed chainage.</span>
      </div>
    );
  }

  return (
    <ul className="alert-list">
      {tickets.map((t) => (
        <li key={t.ticket_id} className="alert-item">
          <div className="alert-main">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span className={`badge prio-${t.priority}`}>{t.priority} PRIORITY</span>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: "var(--ok)",
                  background: "var(--ok-bg)",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                }}
              >
                STATUS: {t.status}
              </span>
            </div>

            <span className="alert-title">
              {t.ticket_id} &mdash; Pipeline: {t.pipeline_id}
              {t.is_simulated && <span className="sim-tag" style={{ marginLeft: 6 }}>Simulated</span>}
            </span>

            <span className="alert-meta" style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <User size={12} /> {t.assigned_crew || "Rapid Response Crew"}
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <Clock size={12} /> {formatDateTime(t.created_at)}
              </span>
            </span>

            <span className="alert-meta" style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--teal-accent)" }}>
              <MapPin size={12} /> Location: Chainage {formatMeters(t.location_estimate?.chainage_meters)}
              {t.location_estimate?.latitude != null && (
                <span>({t.location_estimate.latitude.toFixed(5)}, {t.location_estimate.longitude?.toFixed(5)})</span>
              )}
            </span>

            <div
              style={{
                marginTop: 4,
                padding: "8px 12px",
                background: "rgba(0, 0, 0, 0.25)",
                borderRadius: "6px",
                border: "1px solid var(--border-subtle)",
                fontSize: 12,
                color: "var(--ink-secondary)",
              }}
            >
              {t.description}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
