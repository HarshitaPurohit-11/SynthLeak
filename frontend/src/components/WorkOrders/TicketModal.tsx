import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../services/api";
import { CLASS_NAMES } from "../../lib/labels";
import { formatMeters } from "../../lib/format";
import {
  MAX_CREW, MAX_DESCRIPTION, buildTicketRequest, defaultDescription, defaultPriority, validateTicketForm,
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
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && !submitting) onClose(); };
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
      if (err instanceof ApiError && err.code === "CONFLICT") setServerError("A work order already exists for this alert.");
      else if (err instanceof ApiError && err.details?.length) setServerError(`${err.message} (${err.details.map((d) => d.issue).join("; ")})`);
      else setServerError(err instanceof Error ? err.message : "Could not create the work order.");
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-back" onMouseDown={(e) => { if (e.target === e.currentTarget && !submitting) onClose(); }}>
      <form className="modal" role="dialog" aria-modal="true" aria-labelledby="wo-title" onSubmit={submit} noValidate>
        <h2 id="wo-title">Create work order</h2>
        <dl className="summary">
          <div><dt>Alert</dt><dd>{alert.alert_id}{alert.is_simulated ? " (simulated)" : ""}</dd></div>
          <div><dt>Detected</dt><dd>{CLASS_NAMES[alert.class_label]} on {pipeline?.name ?? alert.pipeline_id}</dd></div>
          <div><dt>Estimated position</dt><dd>{formatMeters(alert.estimated_chainage_meters)} along the pipeline</dd></div>
        </dl>
        <label>Priority
          <select ref={first} value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </label>
        <label>Assigned crew (optional)
          <input value={crew} maxLength={MAX_CREW + 20} onChange={(e) => setCrew(e.target.value)} placeholder="Field Repair Unit Alpha"
            aria-invalid={!!errors.crew} />
          {errors.crew && <span className="err">{errors.crew}</span>}
        </label>
        <label>Description
          <textarea rows={4} value={description} onChange={(e) => setDescription(e.target.value)} aria-invalid={!!errors.description} />
          <span className="hint">{description.trim().length}/{MAX_DESCRIPTION}</span>
          {errors.description && <span className="err">{errors.description}</span>}
        </label>
        {serverError && <div className="form-error" role="alert">{serverError}</div>}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose} disabled={submitting}>Cancel</button>
          <button type="submit" className="btn" disabled={submitting}>{submitting ? "Creating..." : "Create work order"}</button>
        </div>
      </form>
    </div>
  );
}
