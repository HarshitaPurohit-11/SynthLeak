import { useCallback, useEffect, useMemo, useState } from "react";
import { Waves, Map, Bell, ClipboardCheck, AlertCircle } from "lucide-react";
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

  useEffect(() => {
    setSelectedAlertId(null);
  }, [mode]);

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 5000);
    return () => window.clearTimeout(t);
  }, [toast]);

  // Selected alert for map/banner
  const selectedAlert = useMemo(
    () =>
      data.alerts.find((a) => a.alert_id === selectedAlertId) ??
      data.alerts.find((a) => !a.ticket_id) ??
      data.alerts[0] ??
      null,
    [data.alerts, selectedAlertId],
  );

  const bannerRecord = useMemo(() => {
    const f = stream.latest;
    if (!f?.alert.is_alert) return null;
    return (
      data.alerts.find((a) => a.pipeline_id === f.pipeline_id && !a.ticket_id) ??
      data.alerts.find((a) => a.pipeline_id === f.pipeline_id) ??
      null
    );
  }, [data.alerts, stream.latest]);

  const selectedPipeline = data.pipelines.find(
    (p) => p.pipeline_id === (selectedPipelineId ?? selectedAlert?.pipeline_id),
  );
  const modalPipeline = modalAlert
    ? data.pipelines.find((p) => p.pipeline_id === modalAlert.pipeline_id)
    : undefined;

  const onCreated = useCallback((t: Ticket) => {
    setModalAlert(null);
    setTab("orders");
    setToast(`Work Order ${t.ticket_id} successfully dispatched.`);
  }, []);

  const hasSource =
    stream.connection === "live" || stream.connection === "demo" || stream.connection === "demo-paused";

  const empty =
    mode === "demo"
      ? { title: "Starting Scenario Simulator", hint: "Generating synthetic acoustic emission frames..." }
      : stream.connection === "reconnecting"
      ? { title: "Awaiting Live WebSocket Connection", hint: "Connecting to FastAPI backend on port 8000..." }
      : { title: "Live Acoustic Signal Stream Active", hint: "Continuous 44.1 kHz STFT frames arriving at ~15 FPS." };

  return (
    <div className="app">
      <Header
        mode={mode}
        onMode={setMode}
        connection={stream.connection}
        suppress={suppress}
        onSuppress={setSuppress}
        bgReady={bgReady}
      />

      {mode === "demo" && stream.demo && <DemoBar demo={stream.demo} />}

      {mode === "live" && stream.failedAttempts >= 3 && (
        <div
          style={{
            padding: "10px 16px",
            background: "var(--warn-bg)",
            border: "1px solid var(--warn)",
            borderRadius: "10px",
            color: "#fcd34d",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
          role="status"
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <AlertCircle size={18} />
            <span>Live backend server is unreachable. You can launch <code>python -m uvicorn backend.main:app</code> or switch to Demo Simulator.</span>
          </div>
          <button className="btn small light" onClick={() => setMode("demo")}>
            Switch to Demo Simulator
          </button>
        </div>
      )}

      <AlertBanner frame={stream.latest} record={bannerRecord} onCreateTicket={setModalAlert} />

      <main className="grid">
        <section className="left">
          <div className="panel scope">
            <div className="panel-head">
              <h2>
                <Waves size={18} style={{ color: "var(--teal-accent)" }} />
                Acoustic Spectrogram Waterfall (100 Hz &ndash; 10 kHz)
              </h2>
              <span className="panel-sub">
                {stream.latest ? `${stream.latest.pipeline_id} / ${stream.latest.sensor_id}` : "Sensor Standby"}
                {stream.latest?.is_simulated ? " (Simulated)" : ""}
              </span>
            </div>
            <Waterfall
              subscribe={stream.subscribe}
              suppress={suppress}
              hasSource={hasSource}
              emptyTitle={empty.title}
              emptyHint={empty.hint}
              onBackgroundReady={setBgReady}
            />
          </div>

          <TelemetryPanel frame={stream.latest} />
        </section>

        <section className="right">
          <div className="panel mapPanel">
            <div className="panel-head">
              <h2>
                <Map size={18} style={{ color: "var(--teal-accent)" }} />
                Municipal Pipeline GIS Network
              </h2>
              <span className="panel-sub">
                {selectedPipeline
                  ? `${selectedPipeline.name} (${selectedPipeline.material}, ${selectedPipeline.diameter_mm} mm) - ${STATUS_NAMES[selectedPipeline.status]}`
                  : "Select a pipeline segment"}
              </span>
            </div>
            {data.state === "error" && mode === "live" && (
              <div
                style={{
                  padding: "8px 14px",
                  background: "var(--crit-bg)",
                  color: "#fca5a5",
                  fontSize: 12,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
                role="alert"
              >
                <span>{data.error}</span>
                <button className="btn small ghost" onClick={data.refresh}>
                  Retry
                </button>
              </div>
            )}
            <PipelineMap
              pipelines={data.pipelines}
              selectedPipelineId={selectedPipeline?.pipeline_id ?? null}
              selectedAlert={selectedAlert}
              onSelectPipeline={setSelectedPipelineId}
            />
          </div>

          <div className="panel listPanel">
            <div className="tabs" role="tablist">
              <button
                role="tab"
                aria-selected={tab === "alerts"}
                className={tab === "alerts" ? "on" : ""}
                onClick={() => setTab("alerts")}
              >
                <Bell size={14} /> Acoustic Alerts <span className="count">{data.alerts.length}</span>
              </button>
              <button
                role="tab"
                aria-selected={tab === "orders"}
                className={tab === "orders" ? "on" : ""}
                onClick={() => setTab("orders")}
              >
                <ClipboardCheck size={14} /> Work Orders <span className="count">{data.tickets.length}</span>
              </button>
            </div>
            <div className="list-scroll" role="tabpanel">
              {tab === "alerts" ? (
                <AlertList
                  alerts={data.alerts}
                  selectedId={selectedAlert?.alert_id ?? null}
                  onSelect={(a) => {
                    setSelectedAlertId(a.alert_id);
                    setSelectedPipelineId(a.pipeline_id);
                  }}
                  onCreateTicket={setModalAlert}
                />
              ) : (
                <TicketList tickets={data.tickets} />
              )}
            </div>
          </div>
        </section>
      </main>

      {modalAlert && (
        <TicketModal
          alert={modalAlert}
          pipeline={modalPipeline}
          onClose={() => setModalAlert(null)}
          onSubmit={data.createTicket}
          onCreated={onCreated}
        />
      )}

      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </div>
  );
}
