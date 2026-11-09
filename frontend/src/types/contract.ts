// TypeScript mirror of CONTRACT.md v1.0.0. Do not change field names or enums here without
// following the Contract Change Protocol (CONTRIBUTING.md section 3).

export const CLASS_LABELS = ["NORMAL_FLOW", "AMBIENT_URBAN", "PINHOLE_LEAK", "CAVITATION_BURST"] as const;
export type ClassLabel = (typeof CLASS_LABELS)[number];
export type ClassId = 0 | 1 | 2 | 3;
export type Severity = "NONE" | "INFO" | "WARNING" | "CRITICAL";
export type PipelineStatus = "NORMAL" | "WARNING" | "CRITICAL" | "OFFLINE";
export type Priority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type TicketStatus = "OPEN" | "DISPATCHED" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";

// Shared audio constants (shared/constants.py)
export const SAMPLE_RATE = 44100;
export const N_MELS = 128;
export const FILTER_LOW_CUT_HZ = 100;
export const FILTER_HIGH_CUT_HZ = 10000;
export const WS_TARGET_FPS = 15;

// ---- WebSocket (CONTRACT.md section 5) -------------------------------------------------
export interface Classification {
  class_id: ClassId;
  class_label: ClassLabel;
  confidence: number;
  dominant_frequency_hz: number;
}

export interface AlertState {
  is_alert: boolean;
  severity: Severity;
  message: string;
}

export interface SpectrogramFrame {
  message_type: "spectrogram_frame";
  timestamp: string;
  pipeline_id: string;
  sensor_id: string;
  spectrogram_frame: number[]; // exactly N_MELS values in 0..1
  classification: Classification;
  sound_level_db: number;
  alert: AlertState;
  /** Not part of the contract: set only by the in-browser demo replay so the UI can label it. */
  is_simulated?: boolean;
}

export interface Heartbeat {
  message_type: "heartbeat";
  timestamp: string;
  status?: string;
  active_clients?: number;
}

// ---- REST (CONTRACT.md section 6) -------------------------------------------------------
export interface SensorMeta {
  sensor_id: string;
  chainage_meters: number;
  latitude: number;
  longitude: number;
}

export interface Pipeline {
  pipeline_id: string;
  name: string;
  material: string;
  diameter_mm: number;
  length_meters: number;
  status: PipelineStatus;
  sensors: SensorMeta[];
  geometry: { type: "LineString"; coordinates: [number, number][] }; // [lon, lat]
  created_at: string;
  updated_at: string;
}

export interface AlertRecord {
  alert_id: string;
  pipeline_id: string;
  sensor_id: string;
  timestamp: string;
  class_id: ClassId;
  class_label: ClassLabel;
  confidence: number;
  dominant_frequency_hz: number;
  sound_level_db: number;
  severity: Severity;
  estimated_chainage_meters: number | null;
  is_acknowledged: boolean;
  ticket_id: string | null;
  /** UI-only marker for demo replay records. */
  is_simulated?: boolean;
}

export interface LocationEstimate {
  latitude?: number | null;
  longitude?: number | null;
  chainage_meters?: number | null;
}

export interface TicketCreateRequest {
  alert_id: string;
  pipeline_id: string;
  priority: Priority;
  assigned_crew?: string;
  description: string;
  location_estimate?: LocationEstimate;
}

export interface Ticket {
  ticket_id: string;
  alert_id: string;
  pipeline_id: string;
  priority: Priority;
  status: TicketStatus;
  assigned_crew?: string | null;
  description: string;
  location_estimate?: LocationEstimate | null;
  created_at: string;
  updated_at: string;
  is_simulated?: boolean;
}

export interface ListResponse<T> {
  total: number;
  items: T[];
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: { field?: string; issue: string }[]; timestamp: string };
}
