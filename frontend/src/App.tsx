import { useCallback, useEffect, useMemo, useState } from "react";
import AlertList from "./components/Alerts/AlertList";
import AlertBanner from "./components/Layout/AlertBanner";
import DemoBar from "./components/Layout/DemoBar";
import Header from "./components/Layout/Header";
import PipelineMap from "./components/Map/PipelineMap";
import Waterfall from "./components/Spectrogram/Waterfall";
import TelemetryPanel from "./components/Telemetry/TelemetryPanel";
import TicketList from "./components/WorkOrders/TicketList";
import TicketModal from "./components/WorkOrders/TicketModal";
import { useNetworkData } from "./hooks/useNetworkData";
import { useStream, type Mode } from "./hooks/useStream";
import { STATUS_NAMES } from "./lib/labels";
import type { AlertRecord, Ticket } from "./types/contract";

function initialMode(): Mode {
  return new URLSearchParams(window.location.search).get("mode") === "demo" ? "demo" : "live";
}

export default function App() {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [suppress, setSuppress] = useState(false);
  const [bgReady, setBgReady] = useState(false);
  const [tab, setTab] = useState<"alerts" | "orders">("alerts");
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [selectedPipelineId, setSelectedPipelineId] = useState<string | null>(null);
  const [modalAlert, setModalAlert] = useState<AlertRecord | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const stream = useStream(mode);
  const data = useNetworkData(mode, stream.demo, stream.latest);

  useEffect(() => { setSelectedAlertId(null); }, [mode]);
  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 5000);
    return () => window.clearTimeout(t);
  }, [toast]);

  // The alert the banner/map should talk about: the one the user picked, else the newest without a work order.
  const selectedAlert = useMemo(
    () => data.alerts.find((a) => a.alert_id === selectedAlertId) ?? data.alerts.find((a) => !a.ticket_id) ?? data.alerts[0] ?? null,
    [data.alerts, selectedAlertId],
  );
  const bannerRecord = useMemo(() => {
    const f = stream.latest;
    if (!f?.alert.is_alert) return null;
    return data.alerts.find((a) => a.pipeline_id === f.pipeline_id && !a.ticket_id)
      ?? data.alerts.find((a) => a.pipeline_id === f.pipeline_id) ?? null;
  }, [data.alerts, stream.latest]);

  const selectedPipeline = data.pipelines.find((p) => p.pipeline_id === (selectedPipelineId ?? selectedAlert?.pipeline_id));
  const modalPipeline = modalAlert ? data.pipelines.find((p) => p.pipeline_id === modalAlert.pipeline_id) : undefined;

  const onCreated = useCallback((t: Ticket) => {
    setModalAlert(null);
    setTab("orders");
    setToast(`Work order ${t.ticket_id} created.`);
  }, []);

  const hasSource = stream.connection === "live" || stream.connection === "demo" || stream.connection === "demo-paused";
  const empty = mode === "demo"
    ? { title: "Starting demo replay", hint: "Simulated frames will appear in a moment." }
    : stream.connection === "reconnecting"
      ? { title: "Cannot reach the live stream", hint: "Check that the backend is running. Retrying automatically." }
      : { title: "Waiting for audio frames", hint: "Connected to the backend. Frames start as soon as the microphone or scenario replay is running." };

  return (
    <div className="app">
      <Header mode={mode} onMode={setMode} connection={stream.connection} suppress={suppress} onSuppress={setSuppress} bgReady={bgReady} />
      {mode === "demo" && stream.demo && <DemoBar demo={stream.demo} />}
      {mode === "live" && stream.failedAttempts >= 3 && (
        <div className="notice" role="status">
          The live backend is not responding.
          <button className="btn small" onClick={() => setMode("demo")}>Switch to demo replay</button>
        </div>
      )}
      <AlertBanner frame={stream.latest} record={bannerRecord} onCreateTicket={setModalAlert} />

      <main className="grid">
        <section className="left">
          <div className="panel scope">
            <div className="panel-head">
              <h2>Live spectrogram</h2>
              <span className="panel-sub">{stream.latest ? `${stream.latest.pipeline_id} / ${stream.latest.sensor_id}` : "No sensor"}{stream.latest?.is_simulated ? " (simulated)" : ""}</span>
            </div>
            <Waterfall subscribe={stream.subscribe} suppress={suppress} hasSource={hasSource}
              emptyTitle={empty.title} emptyHint={empty.hint} onBackgroundReady={setBgReady} />
          </div>
          <TelemetryPanel frame={stream.latest} />
        </section>

        <section className="right">
          <div className="panel mapPanel">
            <div className="panel-head">
              <h2>Pipeline network</h2>
              <span className="panel-sub">
                {selectedPipeline ? `${selectedPipeline.name} - ${selectedPipeline.material}, ${selectedPipeline.diameter_mm} mm, ${selectedPipeline.length_meters} m - ${STATUS_NAMES[selectedPipeline.status]}` : "Select a pipeline"}
              </span>
            </div>
            {data.state === "error" && mode === "live" && (
              <div className="inline-error" role="alert">
                {data.error} <button className="btn small ghost" onClick={data.refresh}>Retry</button>
              </div>
            )}
            <PipelineMap pipelines={data.pipelines} selectedPipelineId={selectedPipeline?.pipeline_id ?? null}
              selectedAlert={selectedAlert} onSelectPipeline={setSelectedPipelineId} />
          </div>

          <div className="panel listPanel">
            <div className="tabs" role="tablist">
              <button role="tab" aria-selected={tab === "alerts"} className={tab === "alerts" ? "on" : ""} onClick={() => setTab("alerts")}>
                Alerts <span className="count">{data.alerts.length}</span>
              </button>
              <button role="tab" aria-selected={tab === "orders"} className={tab === "orders" ? "on" : ""} onClick={() => setTab("orders")}>
                Work orders <span className="count">{data.tickets.length}</span>
              </button>
            </div>
            <div className="list-scroll" role="tabpanel">
              {tab === "alerts" ? (
                <AlertList alerts={data.alerts} selectedId={selectedAlert?.alert_id ?? null}
                  onSelect={(a) => { setSelectedAlertId(a.alert_id); setSelectedPipelineId(a.pipeline_id); }}
                  onCreateTicket={setModalAlert} />
              ) : (
                <TicketList tickets={data.tickets} />
              )}
            </div>
          </div>
        </section>
      </main>

      {modalAlert && (
        <TicketModal alert={modalAlert} pipeline={modalPipeline} onClose={() => setModalAlert(null)}
          onSubmit={data.createTicket} onCreated={onCreated} />
      )}
      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  );
}
