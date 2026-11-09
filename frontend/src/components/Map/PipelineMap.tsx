import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { pointAtChainage } from "../../lib/geo";
import { STATUS_COLORS, STATUS_NAMES } from "../../lib/labels";
import type { AlertRecord, Pipeline, PipelineStatus } from "../../types/contract";

interface Props {
  pipelines: Pipeline[];
  selectedPipelineId: string | null;
  selectedAlert: AlertRecord | null;
  onSelectPipeline: (id: string) => void;
}

const LEGEND: PipelineStatus[] = ["NORMAL", "WARNING", "CRITICAL", "OFFLINE"];

export default function PipelineMap({ pipelines, selectedPipelineId, selectedAlert, onSelectPipeline }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const pipeLayer = useRef<L.LayerGroup | null>(null);
  const leakLayer = useRef<L.LayerGroup | null>(null);
  const fitted = useRef(false);
  const selectRef = useRef(onSelectPipeline);
  selectRef.current = onSelectPipeline;

  useEffect(() => {
    if (!el.current || map.current) return;
    const m = L.map(el.current, { zoomControl: true, preferCanvas: false }).setView([28.6175, 77.215], 14);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(m);
    pipeLayer.current = L.layerGroup().addTo(m);
    leakLayer.current = L.layerGroup().addTo(m);
    map.current = m;
    const ro = new ResizeObserver(() => m.invalidateSize());
    ro.observe(el.current);
    return () => { ro.disconnect(); m.remove(); map.current = null; };
  }, []);

  useEffect(() => {
    const m = map.current;
    const layer = pipeLayer.current;
    if (!m || !layer) return;
    layer.clearLayers();
    const bounds = L.latLngBounds([]);
    for (const p of pipelines) {
      const latlngs = p.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);
      latlngs.forEach((ll) => bounds.extend(ll));
      const selected = p.pipeline_id === selectedPipelineId;
      const line = L.polyline(latlngs, {
        color: STATUS_COLORS[p.status], weight: selected ? 10 : 6, opacity: 0.95, lineCap: "round",
      }).addTo(layer);
      line.bindTooltip(`${p.name} (${p.pipeline_id}) - ${STATUS_NAMES[p.status]}`, { sticky: true });
      line.on("click", () => selectRef.current(p.pipeline_id));
      for (const s of p.sensors) {
        L.circleMarker([s.latitude, s.longitude], {
          radius: 5, color: "#14232b", weight: 2, fillColor: "#fbfcfb", fillOpacity: 1,
        }).bindTooltip(s.sensor_id).addTo(layer);
      }
    }
    if (!fitted.current && bounds.isValid()) {
      m.fitBounds(bounds, { padding: [24, 24] });
      fitted.current = true;
    }
  }, [pipelines, selectedPipelineId]);

  useEffect(() => {
    const layer = leakLayer.current;
    if (!layer) return;
    layer.clearLayers();
    if (!selectedAlert || selectedAlert.estimated_chainage_meters == null) return;
    const p = pipelines.find((x) => x.pipeline_id === selectedAlert.pipeline_id);
    const pt = p ? pointAtChainage(p, selectedAlert.estimated_chainage_meters) : null;
    if (!pt) return;
    const color = selectedAlert.severity === "CRITICAL" ? "#c8372d" : "#d98a00";
    L.circleMarker([pt.latitude, pt.longitude], { radius: 16, color, weight: 2, fillOpacity: 0.15, fillColor: color }).addTo(layer);
    L.circleMarker([pt.latitude, pt.longitude], { radius: 6, color: "#fff", weight: 2, fillColor: color, fillOpacity: 1 })
      .bindTooltip(`Estimated leak at ${selectedAlert.estimated_chainage_meters.toFixed(1)} m`, { permanent: false })
      .addTo(layer);
  }, [selectedAlert, pipelines]);

  return (
    <div className="map-wrap">
      <div ref={el} className="map" role="application" aria-label="Pipeline network map" />
      <ul className="legend" aria-label="Map legend">
        {LEGEND.map((s) => (
          <li key={s}><i style={{ background: STATUS_COLORS[s] }} />{STATUS_NAMES[s]}</li>
        ))}
        <li><i className="dot" />Sensor</li>
      </ul>
      {pipelines.length === 0 && <div className="map-empty">No pipeline data yet.</div>}
    </div>
  );
}
