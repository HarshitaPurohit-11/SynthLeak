import type { ClassLabel, PipelineStatus, Severity } from "../types/contract";

export const STATUS_NAMES: Record<PipelineStatus, string> = {
  NORMAL: "Normal",
  WARNING: "Warning",
  CRITICAL: "Critical",
  OFFLINE: "Offline",
};

export const STATUS_COLORS: Record<PipelineStatus, string> = {
  NORMAL: "#2e7d32",
  WARNING: "#d98a00",
  CRITICAL: "#c8372d",
  OFFLINE: "#757575",
};

export const CLASS_NAMES: Record<ClassLabel, string> = {
  NORMAL_FLOW: "Normal flow",
  AMBIENT_URBAN: "Ambient noise",
  PINHOLE_LEAK: "Pinhole leak",
  CAVITATION_BURST: "Cavitation burst",
};

export const SEVERITY_NAMES: Record<Severity, string> = {
  NONE: "None",
  INFO: "Info",
  WARNING: "Warning",
  CRITICAL: "Critical",
};

