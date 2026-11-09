import type { Heartbeat, SpectrogramFrame } from "../types/contract";

export function parseFrame(data: unknown): SpectrogramFrame | null {
  if (!data || typeof data !== "object") return null;
  const obj = data as Record<string, unknown>;

  if (obj.message_type !== "spectrogram_frame") return null;
  if (!Array.isArray(obj.spectrogram_frame)) return null;
  if (!obj.classification || typeof obj.classification !== "object") return null;
  if (!obj.alert || typeof obj.alert !== "object") return null;

  return data as SpectrogramFrame;
}

export function parseHeartbeat(data: unknown): Heartbeat | null {
  if (!data || typeof data !== "object") return null;
  const obj = data as Record<string, unknown>;

  if (obj.message_type !== "heartbeat") return null;
  return data as Heartbeat;
}
