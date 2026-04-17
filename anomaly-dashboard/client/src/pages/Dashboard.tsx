import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { AlertTriangle, Activity, Server, FileText, GitBranch, TrendingUp } from "lucide-react";
import { KpiCard, SeverityBadge, ScoreBar, timeAgo, LoadingRows, EmptyState } from "@/components/shared/SeverityBadge";

function CustomTooltip({ active, payload, label }: Record<string, unknown>) {
  if (active && Array.isArray(payload) && payload.length) {
    return (
      <div className="rounded border border-border bg-card p-3 text-xs shadow-lg">
        <p className="text-muted-foreground mb-1">{label as string}</p>
        {(payload as Array<{ name: string; value: number; color: string }>).map((p) => (
          <p key={p.name} style={{ color: p.color }} className="tabular-nums">
            {p.name}: {typeof p.value === "number" ? (p.name.includes("Rate") || p.name.includes("rate") ? (p.value * 100).toFixed(2) + "%" : p.value.toLocaleString()) : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
}

export default function DashboardPage() {
  const { data: overview, isLoading: ovLoading } = useQuery({
    queryKey: ["/api/proxy/overview"],
    queryFn: () => apiRequest("GET", "/api/proxy/overview").then(r => r.json()),
    refetchInterval: 30000,
  });

  const { data: anomalies, isLoading: anomLoading } = useQuery({
    queryKey: ["/api/proxy/anomalies"],
    queryFn: () => apiRequest("GET", "/api/proxy/anomalies").then(r => r.json()),
    refetchInterval: 15000,
  });

  const { data: traffic, isLoading: trafficLoading } = useQuery({
    queryKey: ["/api/proxy/metrics/traffic"],
    queryFn: () => apiRequest("GET", "/api/proxy/metrics/traffic").then(r => r.json()),
    refetchInterval: 30000,
  });

  const trafficData = Array.isArray(traffic)
    ? traffic.map((t: Record<string, unknown>) => ({
        time: new Date(t.timestamp as string).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        requests: t.requestCount as number,
        errorRate: t.errorRate as number,
        latency: t.avgLatencyMs as number,
      }))
    : [];

  const anomalyList = Array.isArray(anomalies) ? anomalies.slice(0, 10) : [];

  const severityCounts = anomalyList.reduce((acc: Record<string, number>, a: Record<string, string>) => {
    const s = a.severity || "NORMAL";
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  const severityDistData = [
    { name: "Critical", value: severityCounts["CRITICAL"] || 0, fill: "#ef4444" },
    { name: "High", value: severityCounts["HIGH"] || 0, fill: "#f97316" },
    { name: "Medium", value: severityCounts["MEDIUM"] || 0, fill: "#eab308" },
    { name: "Low", value: severityCounts["LOW"] || 0, fill: "#22c55e" },
  ];

  return (
    <div className="space-y-5">
      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 card-grid">
        <KpiCard
          label="Active Anomalies"
          value={ovLoading ? "—" : overview?.activeAnomalies ?? 0}
          sub="Require attention"
          accent="critical"
          icon={<AlertTriangle size={14} />}
        />
        <KpiCard
          label="Total Services"
          value={ovLoading ? "—" : overview?.totalServices ?? 0}
          sub={`${overview?.degradedServices ?? 0} degraded`}
          accent={overview?.degradedServices > 0 ? "high" : "low"}
          icon={<Server size={14} />}
        />
        <KpiCard
          label="Metrics Ingested"
          value={ovLoading ? "—" : (overview?.totalMetrics ?? 0).toLocaleString()}
          sub="All time"
          icon={<Activity size={14} />}
        />
        <KpiCard
          label="Log Entries"
          value={ovLoading ? "—" : (overview?.totalLogs ?? 0).toLocaleString()}
          sub="OpenSearch indexed"
          icon={<FileText size={14} />}
        />
        <KpiCard
          label="Trace Spans"
          value={ovLoading ? "—" : (overview?.totalTraces ?? 0).toLocaleString()}
          sub="Distributed traces"
          icon={<GitBranch size={14} />}
        />
        <KpiCard
          label="Total Anomalies"
          value={ovLoading ? "—" : overview?.totalAnomalies ?? 0}
          sub="All time detected"
          accent="info"
          icon={<TrendingUp size={14} />}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Traffic chart */}
        <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-foreground">Request Traffic</h2>
            <span className="text-xs text-muted-foreground">Last 30 min</span>
          </div>
          {trafficLoading ? (
            <div className="h-44 animate-pulse bg-muted rounded" />
          ) : trafficData.length === 0 ? (
            <EmptyState message="No traffic data" />
          ) : (
            <ResponsiveContainer width="100%" height={176}>
              <AreaChart data={trafficData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <defs>
                  <linearGradient id="gradRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(188, 80%, 42%)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(188, 80%, 42%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={40} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="requests" name="Requests" stroke="hsl(188, 80%, 42%)" fill="url(#gradRequests)" strokeWidth={1.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Severity distribution */}
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-foreground">Severity Distribution</h2>
            <span className="text-xs text-muted-foreground">Recent 10</span>
          </div>
          {anomLoading ? (
            <div className="h-44 animate-pulse bg-muted rounded" />
          ) : (
            <ResponsiveContainer width="100%" height={176}>
              <BarChart data={severityDistData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} allowDecimals={false} width={25} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Count" radius={[3, 3, 0, 0]}>
                  {severityDistData.map((entry, idx) => (
                    <rect key={idx} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Error rate chart */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-foreground">Error Rate & Latency</h2>
          <span className="text-xs text-muted-foreground">Last 30 min</span>
        </div>
        {trafficLoading ? (
          <div className="h-32 animate-pulse bg-muted rounded" />
        ) : (
          <ResponsiveContainer width="100%" height={128}>
            <AreaChart data={trafficData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <defs>
                <linearGradient id="gradError" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradLatency" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
              <YAxis yAxisId="left" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={40} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={40} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              <Area yAxisId="left" type="monotone" dataKey="errorRate" name="Error Rate" stroke="#ef4444" fill="url(#gradError)" strokeWidth={1.5} dot={false} />
              <Area yAxisId="right" type="monotone" dataKey="latency" name="Latency (ms)" stroke="#f97316" fill="url(#gradLatency)" strokeWidth={1.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Recent anomalies table */}
      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-foreground">Recent Anomalies</h2>
          <a href="#/alerts" className="text-xs text-primary hover:underline">View all</a>
        </div>
        <div className="overflow-x-auto sticky-thead">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-muted-foreground">
                <th className="text-left px-4 py-2.5 font-medium">Service</th>
                <th className="text-left px-4 py-2.5 font-medium">Endpoint</th>
                <th className="text-left px-4 py-2.5 font-medium">Severity</th>
                <th className="text-left px-4 py-2.5 font-medium">Hybrid Score</th>
                <th className="text-left px-4 py-2.5 font-medium">Status</th>
                <th className="text-left px-4 py-2.5 font-medium">Detected</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {anomLoading ? (
                <LoadingRows cols={6} rows={6} />
              ) : anomalyList.length === 0 ? (
                <tr><td colSpan={6}><EmptyState message="No anomalies detected" /></td></tr>
              ) : (
                anomalyList.map((a: Record<string, unknown>, i: number) => (
                  <tr key={i} className="hover:bg-muted/40 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-xs text-primary">{a.apiName as string}</td>
                    <td className="px-4 py-2.5 text-muted-foreground font-mono text-xs truncate max-w-[160px]">{a.endpoint as string}</td>
                    <td className="px-4 py-2.5"><SeverityBadge severity={a.severity as string} /></td>
                    <td className="px-4 py-2.5 w-36"><ScoreBar score={(a.hybridEnsembleScore || a.hybridScore || 0) as number} /></td>
                    <td className="px-4 py-2.5"><SeverityBadge severity={a.status as string} /></td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums">{timeAgo(a.detectedAt as string)}</td>
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
