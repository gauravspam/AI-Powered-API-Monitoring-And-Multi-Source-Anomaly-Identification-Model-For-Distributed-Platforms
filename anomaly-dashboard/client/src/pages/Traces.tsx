import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useState } from "react";
import { Search } from "lucide-react";
import { LoadingRows, EmptyState, timeAgo } from "@/components/shared/SeverityBadge";
import { Input } from "@/components/ui/input";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";

type Trace = {
  id: number;
  traceId: string;
  spanId: string;
  serviceName: string;
  operationName: string;
  durationMs: number;
  statusCode: number;
  timestamp: string;
  tags?: Record<string, string>;
};

type TracesResponse = {
  content?: Trace[];
  totalElements?: number;
} | Trace[];

export default function TracesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: raw, isLoading } = useQuery<TracesResponse>({
    queryKey: ["/api/proxy/traces"],
    queryFn: () => apiRequest("GET", "/api/proxy/traces").then(r => r.json()),
    refetchInterval: 20000,
  });

  const traces: Trace[] = Array.isArray(raw) ? raw : (raw?.content || []);

  const filtered = traces.filter(t => {
    const matchSearch = !search ||
      t.traceId?.toLowerCase().includes(search.toLowerCase()) ||
      t.serviceName?.toLowerCase().includes(search.toLowerCase()) ||
      t.operationName?.toLowerCase().includes(search.toLowerCase());
    const is5xx = t.statusCode >= 500;
    const matchStatus = statusFilter === "all" ||
      (statusFilter === "error" && is5xx) ||
      (statusFilter === "success" && !is5xx);
    return matchSearch && matchStatus;
  });

  const p50 = traces.length ? [...traces].sort((a, b) => a.durationMs - b.durationMs)[Math.floor(traces.length * 0.5)]?.durationMs : 0;
  const p99 = traces.length ? [...traces].sort((a, b) => a.durationMs - b.durationMs)[Math.floor(traces.length * 0.99)]?.durationMs : 0;
  const errorCount = traces.filter(t => t.statusCode >= 400).length;
  const avgDuration = traces.length ? Math.round(traces.reduce((s, t) => s + t.durationMs, 0) / traces.length) : 0;

  const scatterData = traces.map((t, i) => ({
    x: i,
    y: t.durationMs,
    statusCode: t.statusCode,
    name: t.serviceName,
  }));

  const statusColor = (code: number) => code >= 500 ? "#ef4444" : code >= 400 ? "#f97316" : "#22c55e";

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-3">
        <div className="rounded-lg border border-border bg-card p-3 text-center">
          <div className="text-2xl font-bold tabular-nums text-foreground">{traces.length}</div>
          <div className="text-xs text-muted-foreground mt-0.5">Total Spans</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 text-center">
          <div className="text-2xl font-bold tabular-nums text-foreground">{avgDuration}ms</div>
          <div className="text-xs text-muted-foreground mt-0.5">Avg Duration</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 text-center">
          <div className="text-2xl font-bold tabular-nums text-orange-400">{p99}ms</div>
          <div className="text-xs text-muted-foreground mt-0.5">P99 Latency</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 text-center">
          <div className="text-2xl font-bold tabular-nums text-red-400">{errorCount}</div>
          <div className="text-xs text-muted-foreground mt-0.5">Error Spans</div>
        </div>
      </div>

      {/* Scatter chart: latency distribution */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-foreground">Span Latency Distribution</h2>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block"/>2xx</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-400 inline-block"/>4xx</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block"/>5xx</span>
          </div>
        </div>
        {isLoading ? (
          <div className="h-40 animate-pulse bg-muted rounded" />
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <ScatterChart margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="x" tick={false} axisLine={false} tickLine={false} label={{ value: "Span index", position: "insideBottom", fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
              <YAxis dataKey="y" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={45} unit="ms" />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload?.[0]) {
                    const d = payload[0].payload as { name: string; y: number; statusCode: number };
                    return (
                      <div className="rounded border border-border bg-card p-2 text-xs shadow">
                        <p className="text-primary">{d.name}</p>
                        <p className="text-foreground">{d.y}ms</p>
                        <p className="text-muted-foreground">HTTP {d.statusCode}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter
                data={scatterData}
                fill="#22c55e"
                shape={(props: Record<string, unknown>) => {
                  const { cx, cy, payload } = props as { cx: number; cy: number; payload: { statusCode: number } };
                  return <circle cx={cx} cy={cy} r={3.5} fill={statusColor(payload.statusCode)} opacity={0.8} />;
                }}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search trace ID, service, operation…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-7 h-8 text-sm bg-card font-mono"
            data-testid="input-trace-search"
          />
        </div>
        {["all", "success", "error"].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
              statusFilter === s ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
            data-testid={`button-trace-status-${s}`}
          >
            {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Trace table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto sticky-thead">
          <table className="w-full text-sm font-mono">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground">
                <th className="text-left px-4 py-2.5 font-medium">Trace ID</th>
                <th className="text-left px-4 py-2.5 font-medium">Service</th>
                <th className="text-left px-4 py-2.5 font-medium">Operation</th>
                <th className="text-right px-4 py-2.5 font-medium">Duration</th>
                <th className="text-right px-4 py-2.5 font-medium">Status</th>
                <th className="text-left px-4 py-2.5 font-medium">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <LoadingRows cols={6} rows={8} />
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6}><EmptyState message="No traces found" /></td></tr>
              ) : (
                filtered.map((t, i) => (
                  <tr key={`${t.traceId}-${i}`} className="hover:bg-muted/40 transition-colors" data-testid={`row-trace-${i}`}>
                    <td className="px-4 py-2 text-xs text-muted-foreground truncate max-w-[120px]">{t.traceId}</td>
                    <td className="px-4 py-2 text-xs text-primary">{t.serviceName}</td>
                    <td className="px-4 py-2 text-xs text-foreground truncate max-w-[180px]">{t.operationName}</td>
                    <td className="px-4 py-2 text-right text-xs tabular-nums">
                      <span className={t.durationMs > 1000 ? "text-orange-400" : t.durationMs > 500 ? "text-yellow-400" : "text-foreground"}>
                        {t.durationMs}ms
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <span style={{ color: statusColor(t.statusCode) }} className="text-xs font-semibold tabular-nums">
                        {t.statusCode}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground tabular-nums">{timeAgo(t.timestamp)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
