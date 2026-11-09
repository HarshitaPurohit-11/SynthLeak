import { formatDateTime, formatMeters } from "../../lib/format";
import type { Ticket } from "../../types/contract";

export default function TicketList({ tickets }: { tickets: Ticket[] }) {
  if (tickets.length === 0) {
    return (
      <div className="empty">
        <strong>No work orders in this session</strong>
        <span>Choose an alert and select Create work order to dispatch a field crew.</span>
      </div>
    );
  }
  return (
    <ul className="alert-list">
      {tickets.map((t) => (
        <li key={t.ticket_id} className="alert-item ticket">
          <div className="alert-main static">
            <span className={`badge prio-${t.priority}`}>{t.priority}</span>
            <span className="alert-title">{t.ticket_id} &middot; {t.status}{t.is_simulated ? " (simulated)" : ""}</span>
            <span className="alert-meta">{t.pipeline_id} &middot; {t.assigned_crew || "Unassigned"} &middot; {formatDateTime(t.created_at)}</span>
            <span className="alert-meta">Chainage {formatMeters(t.location_estimate?.chainage_meters)}</span>
            <span className="ticket-desc">{t.description}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
