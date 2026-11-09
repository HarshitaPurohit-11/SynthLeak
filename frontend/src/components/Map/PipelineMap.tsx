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

export default function PipelineMap({
  pipelines,
  selectedPipelineId,
  selectedAlert,
  onSelectPipeline,
}: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const pipeLayer = useRef<L.LayerGroup | null>(null);
  const leakLayer = useRef<L.LayerGroup | null>(null);
  const fitted = useRef(false);
  const selectRef = useRef(onSelectPipeline);
  selectRef.current = onSelectPipeline;

  useEffect(() => {
    if (!el.current || map.current) return;
    
    // Initialize Leaflet Map with dark technical style
    const m = L.map(el.current, { zoomControl: true, preferCanvas: true }).setView(
      [28.6175, 77.215],
      14,
    );

    // CartoDB Dark Matter tile layer for cyber-industrial aesthetic
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        maxZoom: 19,
        subdomains: "abcd",
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      },
    ).addTo(m);

    pipeLayer.current = L.layerGroup().addTo(m);
    leakLayer.current = L.layerGroup().addTo(m);
    map.current = m;

    const ro = new ResizeObserver(() => m.invalidateSize());
    ro.observe(el.current);

    return () => {
      ro.disconnect();
      m.remove();
      map.current = null;
    };
  }, []);

  // Update Pipeline Network Polylines & Sensor Nodes
  useEffect(() => {
    const m = map.current;
    const layer = pipeLayer.current;
    if (!m || !layer) return;
    layer.clearLayers();

    const bounds = L.latLngBounds([]);

    for (const p of pipelines) {
      const latlngs = p.geometry.coordinates.map(
        ([lon, lat]) => [lat, lon] as [number, number],
      );
      latlngs.forEach((ll) => bounds.extend(ll));

      const selected = p.pipeline_id === selectedPipelineId;
      const color = STATUS_COLORS[p.status] || "#06b6d4";

      // Glow backdrop line if selected
      if (selected) {
        L.polyline(latlngs, {
          color,
          weight: 12,
          opacity: 0.35,
          lineCap: "round",
        }).addTo(layer);
      }

      // Main pipe polyline
      const line = L.polyline(latlngs, {
        color,
        weight: selected ? 6 : 4,
        opacity: 0.95,
        lineCap: "round",
      }).addTo(layer);

      line.bindTooltip(
        `<div style="font-family: sans-serif; font-size: 12px; padding: 2px;">
          <strong>${p.name}</strong> (${p.pipeline_id})<br/>
          Status: <span style="color: ${color}; font-weight: 700;">${STATUS_NAMES[p.status]}</span><br/>
          ${p.material} &bull; ${p.diameter_mm} mm &bull; ${p.length_meters} m
        </div>`,
        { sticky: true, className: "custom-leaflet-tooltip" },
      );

      line.on("click", () => selectRef.current(p.pipeline_id));

      // Dual-Sensor nodes
      for (const s of p.sensors) {
        L.circleMarker([s.latitude, s.longitude], {
          radius: 5,
          color: "#080c10",
          weight: 2,
          fillColor: "#38bdf8",
          fillOpacity: 1,
        })
          .bindTooltip(
            `<strong>Sensor Node:</strong> ${s.sensor_id}<br/>Chainage: ${s.chainage_meters} m`,
            { direction: "top" },
          )
          .addTo(layer);
      }
    }

    if (!fitted.current && bounds.isValid()) {
      m.fitBounds(bounds, { padding: [28, 28] });
      fitted.current = true;
    }
  }, [pipelines, selectedPipelineId]);

  // Update Dynamic Leak Marker with TDoA chainage pinpointing
  useEffect(() => {
    const layer = leakLayer.current;
    if (!layer) return;
    layer.clearLayers();

    if (!selectedAlert || selectedAlert.estimated_chainage_meters == null) return;

    const p = pipelines.find((x) => x.pipeline_id === selectedAlert.pipeline_id);
    const pt = p ? pointAtChainage(p, selectedAlert.estimated_chainage_meters) : null;
    if (!pt) return;

    const color = selectedAlert.severity === "CRITICAL" ? "#ef4444" : "#f59e0b";

    // Animated outer sonar pulse ring
    L.circleMarker([pt.latitude, pt.longitude], {
      radius: 24,
      color,
      weight: 1.5,
      fillOpacity: 0.15,
      fillColor: color,
      className: "leaflet-sonar-pulse",
    }).addTo(layer);

    // Inner sharp target dot
    L.circleMarker([pt.latitude, pt.longitude], {
      radius: 7,
      color: "#ffffff",
      weight: 2,
      fillColor: color,
      fillOpacity: 1,
    })
      .bindPopup(
        `<div style="font-family: sans-serif; font-size: 13px;">
          <strong style="color: ${color}">Acoustic Anomaly Pinpoint</strong><br/>
          Pipeline: <strong>${selectedAlert.pipeline_id}</strong><br/>
          Estimated Chainage: <strong>${selectedAlert.estimated_chainage_meters.toFixed(1)} m</strong><br/>
          Coordinates: ${pt.latitude.toFixed(5)}, ${pt.longitude.toFixed(5)}<br/>
          Confidence: ${(selectedAlert.confidence * 100).toFixed(1)}%
        </div>`,
      )
      .bindTooltip(
        `Acoustic Leak Pinpoint (${selectedAlert.estimated_chainage_meters.toFixed(1)} m)`,
        { permanent: false, direction: "top" },
      )
      .addTo(layer);
  }, [selectedAlert, pipelines]);

  return (
    <div className="map-wrap">
      <div ref={el} className="map" role="application" aria-label="Pipeline network GIS map" />
      <ul className="legend" aria-label="Map legend">
        {LEGEND.map((s) => (
          <li key={s}>
            <i style={{ background: STATUS_COLORS[s] }} />
            {STATUS_NAMES[s]}
          </li>
        ))}
        <li>
          <i className="dot" />
          Sensor Node
        </li>
      </ul>
      {pipelines.length === 0 && <div className="map-empty">Loading network topology...</div>}
    </div>
  );
}
