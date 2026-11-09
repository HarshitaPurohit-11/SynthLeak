import { useCallback, useEffect, useRef, useState } from "react";
import { DEMO_PIPELINES, withStatus } from "../demo/fixtures";
import { api, ApiError } from "../services/api";
import type {
  AlertRecord, Pipeline, SpectrogramFrame, Ticket, TicketCreateRequest,
} from "../types/contract";
import type { DemoControls, Mode } from "./useStream";

export type LoadState = "loading" | "ready" | "error";

export interface NetworkData {
  pipelines: Pipeline[];
  alerts: AlertRecord[];
  tickets: Ticket[];
  state: LoadState;
  error: string | null;
  refresh: () => void;
  createTicket: (req: TicketCreateRequest) => Promise<Ticket>;
}

const ALERT_POLL_MS = 5000;
const PIPELINE_POLL_MS = 15000;

function newestFirst(a: AlertRecord[]): AlertRecord[] {
  return [...a].sort((x, y) => (x.timestamp < y.timestamp ? 1 : x.timestamp > y.timestamp ? -1 : 0));
}

export function useNetworkData(mode: Mode, demo: DemoControls | null, latest: SpectrogramFrame | null): NetworkData {
  const [livePipelines, setLivePipelines] = useState<Pipeline[]>([]);
  const [liveAlerts, setLiveAlerts] = useState<AlertRecord[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [demoTicketByAlert, setDemoTicketByAlert] = useState<Record<string, string>>({});
  const demoCounter = useRef(0);

  const fetchPipelines = useCallback(async () => {
    try {
      const res = await api.pipelines();
      setLivePipelines(res.items);
      setState("ready");
      setError(null);
    } catch (e) {
      setState("error");
      setError(e instanceof Error ? e.message : "Could not load pipelines");
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await api.alerts();
      setLiveAlerts(res.items);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load alerts");
    }
  }, []);

  const refresh = useCallback(() => {
    if (mode === "live") { void fetchPipelines(); void fetchAlerts(); }
  }, [mode, fetchPipelines, fetchAlerts]);

  // Live polling
  useEffect(() => {
    if (mode !== "live") return;
    setState("loading");
    setTickets([]);
    void fetchPipelines();
    void fetchAlerts();
    const a = window.setInterval(() => void fetchAlerts(), ALERT_POLL_MS);
    const p = window.setInterval(() => void fetchPipelines(), PIPELINE_POLL_MS);
    return () => { window.clearInterval(a); window.clearInterval(p); };
  }, [mode, fetchPipelines, fetchAlerts]);

  // Pull a fresh alert list right after the stream reports a new alert (the REST record lags the frame).
  const alertFlag = latest?.alert.is_alert ?? false;
  useEffect(() => {
    if (mode !== "live" || !alertFlag) return;
    const t = window.setTimeout(() => { void fetchAlerts(); void fetchPipelines(); }, 800);
    return () => window.clearTimeout(t);
  }, [mode, alertFlag, fetchAlerts, fetchPipelines]);

  // Demo: forget demo tickets when the scenario restarts
  const resetCount = demo?.resetCount ?? 0;
  useEffect(() => {
    if (mode !== "demo") return;
    setTickets([]);
    setDemoTicketByAlert({});
    demoCounter.current = 0;
    setState("ready");
    setError(null);
  }, [mode, resetCount]);

  const createTicket = useCallback(async (req: TicketCreateRequest): Promise<Ticket> => {
    if (mode === "demo") {
      demoCounter.current += 1;
      const now = new Date().toISOString();
      const t: Ticket = {
        ticket_id: `SIM-WO-${String(demoCounter.current).padStart(4, "0")}`,
        alert_id: req.alert_id, pipeline_id: req.pipeline_id, priority: req.priority, status: "OPEN",
        assigned_crew: req.assigned_crew ?? null, description: req.description,
        location_estimate: req.location_estimate ?? null, created_at: now, updated_at: now, is_simulated: true,
      };
      setTickets((prev) => [t, ...prev]);
      setDemoTicketByAlert((prev) => ({ ...prev, [req.alert_id]: t.ticket_id }));
      return t;
    }
    try {
      const t = await api.createTicket(req);
      setTickets((prev) => [t, ...prev]);
      void fetchAlerts();
      return t;
    } catch (e) {
      if (e instanceof ApiError && e.code === "CONFLICT") void fetchAlerts();
      throw e;
    }
  }, [mode, fetchAlerts]);

  if (mode === "demo" && demo) {
    const alerts = newestFirst(demo.alerts).map((a) =>
      demoTicketByAlert[a.alert_id] ? { ...a, ticket_id: demoTicketByAlert[a.alert_id] } : a);
    return {
      pipelines: withStatus(DEMO_PIPELINES, demo.pipelineStatus, new Date().toISOString()),
      alerts, tickets, state: "ready", error: null, refresh, createTicket,
    };
  }
  return { pipelines: livePipelines, alerts: newestFirst(liveAlerts), tickets, state, error, refresh, createTicket };
}
