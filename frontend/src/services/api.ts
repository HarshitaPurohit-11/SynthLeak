import type {
  AlertRecord, ApiErrorBody, ListResponse, Pipeline, Ticket, TicketCreateRequest,
} from "../types/contract";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details?: { field?: string; issue: string }[]) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", Accept: "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Cannot reach the backend. Check that it is running on port 8000.");
  }
  if (!res.ok) {
    let body: Partial<ApiErrorBody> = {};
    try { body = (await res.json()) as ApiErrorBody; } catch { /* non-JSON error body */ }
    const e = body.error;
    throw new ApiError(res.status, e?.code ?? "HTTP_ERROR", e?.message ?? `Request failed (${res.status})`, e?.details);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status?: string }>("/health"),
  pipelines: (limit = 200) => request<ListResponse<Pipeline>>(`/pipelines?limit=${limit}`),
  alerts: (limit = 50) => request<ListResponse<AlertRecord>>(`/alerts?limit=${limit}`),
  createTicket: (body: TicketCreateRequest) =>
    request<Ticket>("/tickets", { method: "POST", body: JSON.stringify(body) }),
};

export function wsUrl(): string {
  const override = import.meta.env.VITE_WS_STREAM_URL as string | undefined;
  if (override) return override;
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws/stream`;
}
