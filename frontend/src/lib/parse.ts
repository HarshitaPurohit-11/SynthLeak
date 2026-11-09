import type { Heartbeat, SpectrogramFrame } from "../types/contract";

export function parseFrame(data: unknown): SpectrogramFrame | null {
  if (typeof data !== "object" || data === null) return null;
  const obj = data as Record<string, unknown>;

  if (obj.message_type !== "spectrogram_frame" && obj.type !== "spectrogram_frame") {
    return null;
  }
  if (!Array.isArray(obj.spectrogram_frame)) {
    return null;
  }
  return data as SpectrogramFrame;
}

export function parseHeartbeat(data: unknown): Heartbeat | null {
  if (typeof data !== "object" || data === null) return null;
  const obj = data as Record<string, unknown>;

  if (
    obj.message_type === "heartbeat" ||
    obj.type === "heartbeat" ||
    obj.message_type === "pong" ||
    obj.type === "pong" ||
    obj.status === "OK"
  ) {
    return data as Heartbeat;
  }
  return null;
}

