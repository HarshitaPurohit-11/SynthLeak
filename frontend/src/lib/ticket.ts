import type { AlertRecord, Pipeline, Priority, TicketCreateRequest } from "../types/contract";
import { pointAtChainage } from "./geo";

export const MAX_CREW = 100;
export const MAX_DESCRIPTION = 500;

export function defaultPriority(alert: AlertRecord): Priority {
  if (alert.severity === "CRITICAL") return "CRITICAL";
  if (alert.severity === "WARNING") return "HIGH";
  if (alert.severity === "INFO") return "MEDIUM";
  return "LOW";
}

export function defaultDescription(alert: AlertRecord, pipeline?: Pipeline): string {
  const pipeName = pipeline?.name ?? alert.pipeline_id;
  const kind =
    alert.class_label === "PINHOLE_LEAK"
      ? "pinhole orifice leak"
      : alert.class_label === "CAVITATION_BURST"
      ? "cavitation burst / transient"
      : alert.class_label.replace("_", " ").toLowerCase();
  const pos =
    alert.estimated_chainage_meters != null
      ? ` near chainage ${alert.estimated_chainage_meters.toFixed(1)}m`
      : "";
  return `Acoustic detection identified ${kind} on ${pipeName}${pos}. Field inspection and clamp/repair dispatch required.`;
}

export function validateTicketForm(description: string, crew: string): Record<string, string> {
  const errors: Record<string, string> = {};
  const trimmedDesc = description.trim();

  if (!trimmedDesc) {
    errors.description = "A description is required for dispatch.";
  } else if (trimmedDesc.length > MAX_DESCRIPTION) {
    errors.description = `Description must not exceed ${MAX_DESCRIPTION} characters.`;
  }

  if (crew && crew.length > MAX_CREW) {
    errors.crew = `Crew assignment name must not exceed ${MAX_CREW} characters.`;
  }

  return errors;
}

export function buildTicketRequest(
  alert: AlertRecord,
  pipeline: Pipeline | undefined,
  priority: Priority,
  crew: string,
  description: string,
): TicketCreateRequest {
  const req: TicketCreateRequest = {
    alert_id: alert.alert_id,
    pipeline_id: alert.pipeline_id,
    priority,
    description: description.trim(),
  };

  if (crew.trim()) {
    req.assigned_crew = crew.trim();
  }

  if (alert.estimated_chainage_meters != null) {
    let lat: number | undefined;
    let lon: number | undefined;

    if (pipeline) {
      const pt = pointAtChainage(pipeline, alert.estimated_chainage_meters);
      if (pt) {
        lat = Number(pt.latitude.toFixed(6));
        lon = Number(pt.longitude.toFixed(6));
      }
    }

    req.location_estimate = {
      chainage_meters: alert.estimated_chainage_meters,
      latitude: lat,
      longitude: lon,
    };
  }

  return req;
}
