import type { Heartbeat, SpectrogramFrame } from "../types/contract";

export function parseFrame(data: unknown): SpectrogramFrame | null {
  if (!data || typeof data !== "object") return null;
  const obj = data as Record<string, unknown>;

  const msgType = obj.message_type ?? obj.type;
  if (msgType !== "spectrogram_frame") return null;
  if (!Array.isArray(obj.spectrogram_frame)) return null;
  if (!obj.classification || typeof obj.classification !== "object") return null;
  if (!obj.alert || typeof obj.alert !== "object") return null;

  return data as SpectrogramFrame;
}

export function parseHeartbeat(data: unknown): Heartbeat | null {
  if (!data || typeof data !== "object") return null;
  const obj = data as Record<string, unknown>;

  const msgType = obj.message_type ?? obj.type;
  if (msgType === "heartbeat" || msgType === "pong" || obj.status === "OK") {
    return data as Heartbeat;
  }
  return null;
}
