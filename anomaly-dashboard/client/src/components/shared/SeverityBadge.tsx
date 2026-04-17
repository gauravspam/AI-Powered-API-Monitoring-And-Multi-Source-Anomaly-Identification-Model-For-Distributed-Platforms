export function SeverityBadge({ severity }: { severity: string }) {
  const s = (severity || "NORMAL").toUpperCase();
  const cls: Record<string, string> = {
    CRITICAL: "badge-critical",
    HIGH: "badge-high",
    MEDIUM: "badge-medium",
    LOW: "badge-low",
    NORMAL: "badge-normal",
    ACTIVE: "badge-critical",
    ACKNOWLEDGED: "badge-medium",
    RESOLVED: "badge-low",
    ERROR: "badge-critical",
    WARN: "badge-high",
    WARNING: "badge-high",
    INFO: "badge-info",
    DEBUG: "badge-normal",
    FATAL: "badge-critical",
  };
  return (
    <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium tabular-nums ${cls[s] || "badge-normal"}`}>
      {s}
    </span>
  );
}

export function StatusDot({ status }: { status: string }) {
  const s = (status || "").toLowerCase();
  const colorMap: Record<string, string> = {
    healthy: "bg-green-500",
    online: "bg-green-500",
    active: "bg-red-500",
    degraded: "bg-yellow-500",
    down: "bg-red-500",
    offline: "bg-gray-500",
    acknowledged: "bg-yellow-500",
    resolved: "bg-green-500",
  };
  return (
    <span className={`inline-block w-2 h-2 rounded-full ${colorMap[s] || "bg-gray-500"}`} />
  );
}

export function ScoreBar({ score, max = 1 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color = score >= 0.8 ? "#ef4444" : score >= 0.6 ? "#f97316" : score >= 0.4 ? "#eab308" : score >= 0.2 ? "#22c55e" : "#6b7280";
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs tabular-nums w-9 text-right text-muted-foreground">{score.toFixed(3)}</span>
    </div>
  );
}

export function KpiCard({
  label,
  value,
  sub,
  accent,
  icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "critical" | "high" | "medium" | "low" | "info" | "default";
  icon?: React.ReactNode;
}) {
  const accentColor: Record<string, string> = {
    critical: "text-red-400",
    high: "text-orange-400",
    medium: "text-yellow-400",
    low: "text-green-400",
    info: "text-blue-400",
    default: "text-primary",
  };
  return (
    <div className="rounded-lg border border-border bg-card p-4 flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">{label}</span>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </div>
      <span className={`text-2xl font-bold tabular-nums ${accentColor[accent || "default"]}`}>{value}</span>
      {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center gap-2">
      <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
        <span className="text-muted-foreground text-lg">∅</span>
      </div>
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

export function LoadingRows({ cols = 5, rows = 5 }: { cols?: number; rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i}>
          {Array.from({ length: cols }).map((__, j) => (
            <td key={j} className="px-4 py-2.5">
              <div className="h-3 rounded bg-muted animate-pulse" style={{ width: `${60 + Math.random() * 30}%` }} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}
