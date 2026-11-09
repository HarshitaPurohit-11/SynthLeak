// Demo-replay fixtures. EVERYTHING in this folder is simulated and is labelled as such in the UI.
// Geometry/ids follow shared/examples/pipeline_geojson.json so the shapes match the real contract.
import type { Pipeline, PipelineStatus, SensorMeta } from "../types/contract";

type LonLat = [number, number];
const CREATED = "2026-11-01T00:00:00.000Z";

function sensorsFor(prefix: string, coords: LonLat[], length: number): SensorMeta[] {
  const first = coords[0];
  const last = coords[coords.length - 1];
  return [
    { sensor_id: `SENSOR-${prefix}1`, chainage_meters: 0, latitude: first[1], longitude: first[0] },
    { sensor_id: `SENSOR-${prefix}2`, chainage_meters: length, latitude: last[1], longitude: last[0] },
  ];
}

function pipe(
  id: string, name: string, material: string, diameter: number, length: number, prefix: string, coords: LonLat[],
): Pipeline {
  return {
    pipeline_id: id, name, material, diameter_mm: diameter, length_meters: length, status: "NORMAL",
    sensors: sensorsFor(prefix, coords, length),
    geometry: { type: "LineString", coordinates: coords },
    created_at: CREATED, updated_at: CREATED,
  };
}

export const DEMO_PIPELINES: Pipeline[] = [
  pipe("PIPE-001", "Main Distribution Trunk A", "Ductile Iron", 300, 1250, "A",
    [[77.209, 28.6139], [77.214, 28.6175], [77.2185, 28.621]]),
  pipe("PIPE-002", "Gas Distribution Line G-2", "Steel", 200, 820, "B",
    [[77.2185, 28.621], [77.223, 28.624], [77.2285, 28.6262]]),
  pipe("PIPE-003", "Eastern Feeder B", "PVC", 160, 910, "C",
    [[77.2185, 28.621], [77.2215, 28.617], [77.226, 28.614]]),
  pipe("PIPE-004", "Market Street Branch", "HDPE", 110, 690, "D",
    [[77.214, 28.6175], [77.211, 28.6205], [77.2085, 28.624]]),
  pipe("PIPE-005", "Gas Service Main G-5", "Steel", 150, 700, "E",
    [[77.209, 28.6139], [77.205, 28.611], [77.201, 28.6095]]),
  pipe("PIPE-006", "Old Town Cast Iron C", "Cast Iron", 250, 880, "F",
    [[77.209, 28.6139], [77.2065, 28.618], [77.204, 28.6215]]),
  pipe("PIPE-007", "Hospital Loop D", "Ductile Iron", 200, 760, "G",
    [[77.2285, 28.6262], [77.232, 28.623], [77.234, 28.6185]]),
  pipe("PIPE-008", "Canal Crossing E", "Steel", 300, 640, "H",
    [[77.226, 28.614], [77.23, 28.612], [77.235, 28.611]]),
];

export function withStatus(pipelines: Pipeline[], overrides: Record<string, PipelineStatus>, nowIso: string): Pipeline[] {
  return pipelines.map((p) => {
    const status = overrides[p.pipeline_id] ?? p.status;
    return status === p.status ? p : { ...p, status, updated_at: nowIso };
  });
}
