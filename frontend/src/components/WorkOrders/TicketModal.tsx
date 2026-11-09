import { useEffect, useRef, useState } from "react";
import { Wrench, AlertTriangle, Users, FileText, Check, X } from "lucide-react";
import { ApiError } from "../../services/api";
import { CLASS_NAMES } from "../../lib/labels";
import { formatMeters } from "../../lib/format";
import {
  MAX_CREW,
  MAX_DESCRIPTION,
  buildTicketRequest,
  defaultDescription,
  defaultPriority,
  validateTicketForm,
} from "../../lib/ticket";
import type { AlertRecord, Pipeline, Priority, Ticket, TicketCreateRequest } from "../../types/contract";

interface Props {
  alert: AlertRecord;
  pipeline?: Pipeline;
  onClose: () => void;
  onSubmit: (req: TicketCreateRequest) => Promise<Ticket>;
  onCreated: (t: Ticket) => void;
}

const PRIORITIES: Priority[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

const CREW_PRESETS = [
  "Field Repair Unit Alpha",
  "Rapid Acoustic Inspection Team",
  "Emergency Clamp Crew 3",
  "Ultrasonic Verification Squad",
];

export default function TicketModal({ alert, pipeline, onClose, onSubmit, onCreated }: Props) {
  const [priority, setPriority] = useState<Priority>(defaultPriority(alert));
  const [crew, setCrew] = useState("");
  const [description, setDescription] = useState(defaultDescription(alert, pipeline));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const first = useRef<HTMLSelectElement>(null);

  useEffect(() => {
    first.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !submitting) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, submitting]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validateTicketForm(description, crew);
    setErrors(errs);
    if (Object.keys(errs).length) return;

    setSubmitting(true);
    setServerError(null);

    try {
      const t = await onSubmit(buildTicketRequest(alert, pipeline, priority, crew, description));
      onCreated(t);
    } catch (err) {
      if (err instanceof ApiError && err.code === "CONFLICT") {
        setServerError("A work order already exists for this alert.");
      } else if (err instanceof ApiError && err.details?.length) {
        setServerError(`${err.message} (${err.details.map((d) => d.issue).join("; ")})`);
      } else {
        setServerError(err instanceof Error ? err.message : "Could not create the work order.");
      }
      setSubmitting(false);
    }
  }

  return (
    <div
      className="modal-back"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !submitting) onClose();
      }}
    >
      <form
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="wo-title"
        onSubmit={submit}
        noValidate
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 id="wo-title" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Wrench size={22} style={{ color: "var(--teal-accent)" }} />
            Dispatch Work Order
          </h2>
          <button type="button" onClick={onClose} style={{ color: "var(--ink-muted)" }}>
            <X size={20} />
          </button>
        </div>

        <dl className="summary">
          <div>
            <dt>Alert Ref</dt>
            <dd>{alert.alert_id}{alert.is_simulated ? " (simulated)" : ""}</dd>
          </div>
          <div>
            <dt>Classification</dt>
            <dd>{CLASS_NAMES[alert.class_label]}</dd>
          </div>
          <div>
            <dt>Pipeline Asset</dt>
            <dd>{pipeline?.name ?? alert.pipeline_id}</dd>
          </div>
          <div>
            <dt>TDoA Chainage</dt>
            <dd>{formatMeters(alert.estimated_chainage_meters)}</dd>
          </div>
        </dl>

        <label>
          Priority Level
          <select
            ref={first}
            value={priority}
            onChange={(e) => setPriority(e.target.value as Priority)}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Users size={14} /> Assigned Maintenance Crew (Optional)
          </span>
          <input
            value={crew}
            maxLength={MAX_CREW}
            onChange={(e) => setCrew(e.target.value)}
            placeholder="Field Repair Unit Alpha"
            aria-invalid={!!errors.crew}
          />
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
            {CREW_PRESETS.map((p) => (
              <button
                key={p}
                type="button"
                className="btn small ghost"
                style={{ fontSize: 11, padding: "2px 8px" }}
                onClick={() => setCrew(p)}
              >
                + {p}
              </button>
            ))}
          </div>
          {errors.crew && <span className="err">{errors.crew}</span>}
        </label>

        <label>
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <FileText size={14} /> Maintenance Description & Instructions
          </span>
          <textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            aria-invalid={!!errors.description}
          />
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            {errors.description ? (
              <span className="err">{errors.description}</span>
            ) : <span />}
            <span style={{ fontSize: 11, color: "var(--ink-muted)" }}>
              {description.trim().length} / {MAX_DESCRIPTION}
            </span>
          </div>
        </label>

        {serverError && (
          <div
            style={{
              padding: "10px 14px",
              background: "var(--crit-bg)",
              border: "1px solid var(--crit)",
              borderRadius: "8px",
              color: "#fca5a5",
              fontSize: "13px",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
            role="alert"
          >
            <AlertTriangle size={16} />
            {serverError}
          </div>
        )}

        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn" disabled={submitting}>
            {submitting ? "Dispatching..." : <><Check size={16} /> Dispatch Ticket</>}
          </button>
        </div>
      </form>
    </div>
  );
}
