import type { Pipeline } from "../types/contract";

export function haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000; // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export const distanceMeters = (lon1: number, lat1: number, lon2: number, lat2: number): number =>
  haversineMeters(lat1, lon1, lat2, lon2);

/**
 * Finds the GPS latitude and longitude coordinate along a pipeline at a specified chainage distance (meters).
 */
export function pointAtChainage(
  pipeline: Pipeline,
  chainageMeters: number,
): { latitude: number; longitude: number } | null {
  const coords = pipeline.geometry?.coordinates;
  if (!coords || coords.length === 0) return null;
  if (coords.length === 1 || chainageMeters <= 0) {
    return { latitude: coords[0][1], longitude: coords[0][0] };
  }

  const target = Math.max(0, Math.min(chainageMeters, pipeline.length_meters));
  const segmentLengths: number[] = [];
  let totalCalculated = 0;

  for (let i = 0; i < coords.length - 1; i++) {
    const [lon1, lat1] = coords[i];
    const [lon2, lat2] = coords[i + 1];
    const d = haversineMeters(lat1, lon1, lat2, lon2);
    segmentLengths.push(d);
    totalCalculated += d;
  }

  // Scale factor in case line vertices don't exactly equal metadata length_meters
  const scale = totalCalculated > 0 ? totalCalculated / (pipeline.length_meters || totalCalculated) : 1;
  const scaledTarget = target * scale;

  let accumulated = 0;
  for (let i = 0; i < segmentLengths.length; i++) {
    const segLen = segmentLengths[i];
    if (accumulated + segLen >= scaledTarget || i === segmentLengths.length - 1) {
      const segT = segLen > 0 ? (scaledTarget - accumulated) / segLen : 0;
      const clampedT = Math.min(1, Math.max(0, segT));
      const [lon1, lat1] = coords[i];
      const [lon2, lat2] = coords[i + 1];

      return {
        latitude: lat1 + (lat2 - lat1) * clampedT,
        longitude: lon1 + (lon2 - lon1) * clampedT,
      };
    }
    accumulated += segLen;
  }

  const [lastLon, lastLat] = coords[coords.length - 1];
  return { latitude: lastLat, longitude: lastLon };
}
