import type { ClassLabel, PipelineStatus, Severity } from "../types/contract";

export const CLASS_NAMES: Record<ClassLabel, string> = {
  NORMAL_FLOW: "Normal Flow",
  AMBIENT_URBAN: "Ambient Urban Noise",
  PINHOLE_LEAK: "Pinhole Leak",
  CAVITATION_BURST: "Cavitation / Burst",
};

export const SEVERITY_NAMES: Record<Severity, string> = {
  NONE: "Normal",
  INFO: "Information",
  WARNING: "Warning",
  CRITICAL: "Critical",
};

export const STATUS_NAMES: Record<PipelineStatus, string> = {
  NORMAL: "Normal Operating",
  WARNING: "Acoustic Warning",
  CRITICAL: "Critical Alarm",
  OFFLINE: "Offline",
};

export const STATUS_COLORS: Record<PipelineStatus, string> = {
  NORMAL: "#10b981",
  WARNING: "#f59e0b",
  CRITICAL: "#ef4444",
  OFFLINE: "#64748b",
};
