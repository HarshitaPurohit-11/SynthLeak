import { parseFrame, parseHeartbeat } from "../lib/parse";
import type { SpectrogramFrame } from "../types/contract";

export type WsStatus = "connecting" | "open" | "reconnecting";

export interface WsHandlers {
  onFrame: (f: SpectrogramFrame) => void;
  onHeartbeat?: () => void;
  onStatus: (s: WsStatus) => void;
}

const STALE_MS = 15000; // heartbeat is every 5 s per the contract
const MAX_BACKOFF = 10000;

/** WebSocket client with automatic reconnect (exponential backoff) and stale-connection detection. */
export class WsClient {
  private ws: WebSocket | null = null;
  private stopped = false;
  private attempts = 0;
  private lastMessage = 0;
  private retryTimer: number | undefined;
  private watchdog: number | undefined;

  constructor(private url: string, private h: WsHandlers) {}

  start(): void {
    this.stopped = false;
    this.connect();
    this.watchdog = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN && Date.now() - this.lastMessage > STALE_MS) {
        this.ws.close(); // triggers onclose -> reconnect
      }
    }, 5000);
  }

  stop(): void {
    this.stopped = true;
    window.clearTimeout(this.retryTimer);
    window.clearInterval(this.watchdog);
    this.ws?.close();
    this.ws = null;
  }

  private connect(): void {
    this.h.onStatus(this.attempts === 0 ? "connecting" : "reconnecting");
    let ws: WebSocket;
    try {
      ws = new WebSocket(this.url);
    } catch {
      this.scheduleRetry();
      return;
    }
    this.ws = ws;
    ws.onopen = () => {
      this.attempts = 0;
      this.lastMessage = Date.now();
      this.h.onStatus("open");
    };
    ws.onmessage = (ev) => {
      this.lastMessage = Date.now();
      let data: unknown;
      try { data = JSON.parse(ev.data as string); } catch { return; }
      const frame = parseFrame(data);
      if (frame) { this.h.onFrame(frame); return; }
      if (parseHeartbeat(data)) this.h.onHeartbeat?.();
    };
    ws.onclose = () => { if (!this.stopped) this.scheduleRetry(); };
    ws.onerror = () => ws.close();
  }

  private scheduleRetry(): void {
    this.attempts += 1;
    this.h.onStatus("reconnecting");
    const delay = Math.min(MAX_BACKOFF, 1000 * 2 ** Math.min(this.attempts - 1, 4));
    this.retryTimer = window.setTimeout(() => { if (!this.stopped) this.connect(); }, delay);
  }
}
