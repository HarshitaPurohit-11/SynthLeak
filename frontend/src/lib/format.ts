export function formatKHz(hz: number | null | undefined): string {
  if (hz == null || isNaN(hz)) return "--";
  return (hz / 1000).toFixed(2);
}

export function formatMeters(m: number | null | undefined, fallback: string = "Unknown"): string {
  if (m == null || isNaN(m)) return fallback;
  return `${m.toFixed(1)} m`;
}

export function formatPercent(c: number | null | undefined): string {
  if (c == null || isNaN(c)) return "--";
  return `${Math.round(c * 100)}%`;
}

export function formatDateTime(ts: string | null | undefined): string {
  if (!ts) return "--";
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return ts;
    return (
      d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }) +
      " (" +
      (d.getMonth() + 1).toString().padStart(2, "0") +
      "/" +
      d.getDate().toString().padStart(2, "0") +
      ")"
    );
  } catch {
    return ts;
  }
}
