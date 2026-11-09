import type { Pipeline } from "../types/contract";

function distanceMeters(lon1: number, lat1: number, lon2: number, lat2: number): number {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export function pointAtChainage(
  pipeline: Pipeline,
  chainageMeters: number,
): { latitude: number; longitude: number } | null {
  const coords = pipeline.geometry?.coordinates;
  if (!coords || coords.length === 0) return null;
  if (coords.length === 1 || chainageMeters <= 0) {
    return { latitude: coords[0][1], longitude: coords[0][0] };
  }

  const segLengths: number[] = [];
  let totalGeoLen = 0;
  for (let i = 0; i < coords.length - 1; i++) {
    const d = distanceMeters(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]);
    segLengths.push(d);
    totalGeoLen += d;
  }

  const scale = totalGeoLen > 0 && pipeline.length_meters > 0 ? totalGeoLen / pipeline.length_meters : 1.0;
  const targetDist = Math.max(0, Math.min(chainageMeters * scale, totalGeoLen));

  let accumulated = 0;
  for (let i = 0; i < segLengths.length; i++) {
    const len = segLengths[i];
    if (accumulated + len >= targetDist || i === segLengths.length - 1) {
      const frac = len > 0 ? (targetDist - accumulated) / len : 0;
      const lon = coords[i][0] + (coords[i + 1][0] - coords[i][0]) * frac;
      const lat = coords[i][1] + (coords[i + 1][1] - coords[i][1]) * frac;
      return { latitude: lat, longitude: lon };
    }
    accumulated += len;
  }

  const last = coords[coords.length - 1];
  return { latitude: last[1], longitude: last[0] };
}

