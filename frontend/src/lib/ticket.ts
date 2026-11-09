import { pointAtChainage } from "./geo";
import type { AlertRecord, Pipeline, Priority, TicketCreateRequest } from "../types/contract";

export const MAX_CREW = 64;
export const MAX_DESCRIPTION = 500;

export function defaultPriority(alert: AlertRecord): Priority {
  if (alert.severity === "CRITICAL") return "CRITICAL";
  if (alert.severity === "WARNING") return "HIGH";
  if (alert.severity === "INFO") return "MEDIUM";
  return "LOW";
}

export function defaultDescription(alert: AlertRecord, pipeline?: Pipeline): string {
  const pipeName = pipeline?.name ?? alert.pipeline_id;
  const label = alert.class_label.replace("_", " ").toLowerCase();
  const chainage =
    alert.estimated_chainage_meters != null
      ? ` near chainage ${alert.estimated_chainage_meters.toFixed(0)} m`
      : "";
  return `Acoustic detection indicated ${label} on ${pipeName}${chainage}. Physical inspection and verification required.`;
}

export function validateTicketForm(description: string, crew: string): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!description.trim()) {
    errors.description = "Description is required.";
  } else if (description.length > MAX_DESCRIPTION) {
    errors.description = `Description cannot exceed ${MAX_DESCRIPTION} characters.`;
  }
  if (crew && crew.length > MAX_CREW) {
    errors.crew = `Crew name cannot exceed ${MAX_CREW} characters.`;
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
  const pt =
    alert.estimated_chainage_meters != null && pipeline
      ? pointAtChainage(pipeline, alert.estimated_chainage_meters)
      : null;

  return {
    alert_id: alert.alert_id,
    pipeline_id: alert.pipeline_id,
    priority,
    assigned_crew: crew.trim() || undefined,
    description: description.trim(),
    location_estimate:
      alert.estimated_chainage_meters != null
        ? {
            chainage_meters: alert.estimated_chainage_meters,
            latitude: pt?.latitude,
            longitude: pt?.longitude,
          }
        : undefined,
  };
}

