export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "--";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return String(iso);
  }
}

export function formatKHz(hz: number | null | undefined): string {
  if (hz == null || isNaN(hz)) return "--";
  return (hz / 1000).toFixed(1);
}

export function formatMeters(m: number | null | undefined): string {
  if (m == null || isNaN(m)) return "--";
  return `${m.toFixed(1)} m`;
}

export function formatPercent(p: number | null | undefined): string {
  if (p == null || isNaN(p)) return "--";
  return `${(p * 100).toFixed(1)}%`;
}

