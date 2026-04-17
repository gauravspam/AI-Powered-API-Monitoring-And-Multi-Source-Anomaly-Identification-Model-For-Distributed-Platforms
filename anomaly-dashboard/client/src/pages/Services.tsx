import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useState } from "react";
import { Search } from "lucide-react";
import { SeverityBadge, StatusDot, LoadingRows, EmptyState } from "@/components/shared/SeverityBadge";
import { Input } from "@/components/ui/input";

type Service = {
  id: number;
  name: string;
  ownerTeam: string;
  environment: string;
  status: string;
  avgLatencyMs: number;
  errorRate: number;
  anomalyRate: number;
  requestPerMin: number;
};

export default function ServicesPage() {
  const [search, setSearch] = useState("");
  const [envFilter, setEnvFilter] = useState("all");

  const { data: services, isLoading } = useQuery<Service[]>({
    queryKey: ["/api/proxy/services"],
    queryFn: () => apiRequest("GET", "/api/proxy/services").then(r => r.json()),
    refetchInterval: 30000,
  });

  const filtered = (services || []).filter(s => {
    const matchSearch = s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.ownerTeam.toLowerCase().includes(search.toLowerCase());
    const matchEnv = envFilter === "all" || s.environment === envFilter;
    return matchSearch && matchEnv;
  });

  const healthy = (services || []).filter(s => s.status === "healthy").length;
  const degraded = (services || []).filter(s => s.status === "degraded").length;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg border border-border bg-card p-3 text-center">
          <div className="text-2xl font-bold text-foreground tabular-nums">{(services || []).length}</div>
          <div className="text-xs text-muted-foreground mt-0.5">Total Services</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 text-center">
          <div className="text-2xl font-bold text-green-400 tabular-nums">{healthy}</div>
          <div className="text-xs text-muted-foreground mt-0.5">Healthy</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 text-center">
          <div className="text-2xl font-bold text-yellow-400 tabular-nums">{degraded}</div>
          <div className="text-xs text-muted-foreground mt-0.5">Degraded</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search services…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-7 h-8 text-sm bg-card"
            data-testid="input-service-search"
          />
        </div>
        <div className="flex gap-1">
          {["all", "production", "staging"].map(env => (
            <button
              key={env}
              onClick={() => setEnvFilter(env)}
              className={`px-3 py-1.5 text-xs rounded font-medium transition-colors ${
                envFilter === env
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
              data-testid={`button-env-${env}`}
            >
              {env === "all" ? "All Envs" : env.charAt(0).toUpperCase() + env.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto sticky-thead">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground">
                <th className="text-left px-4 py-2.5 font-medium">Service</th>
                <th className="text-left px-4 py-2.5 font-medium">Team</th>
                <th className="text-left px-4 py-2.5 font-medium">Environment</th>
                <th className="text-left px-4 py-2.5 font-medium">Status</th>
                <th className="text-right px-4 py-2.5 font-medium">Avg Latency</th>
                <th className="text-right px-4 py-2.5 font-medium">Error Rate</th>
                <th className="text-right px-4 py-2.5 font-medium">Anomaly Rate</th>
                <th className="text-right px-4 py-2.5 font-medium">Req/min</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <LoadingRows cols={8} rows={5} />
              ) : filtered.length === 0 ? (
                <tr><td colSpan={8}><EmptyState message="No services found" /></td></tr>
              ) : (
                filtered.map(s => (
                  <tr key={s.id} className="hover:bg-muted/40 transition-colors" data-testid={`row-service-${s.id}`}>
                    <td className="px-4 py-2.5 font-mono text-xs text-primary font-medium">{s.name}</td>
                    <td className="px-4 py-2.5 text-muted-foreground text-xs">{s.ownerTeam}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-xs ${s.environment === "production" ? "badge-info" : "badge-normal"} rounded px-1.5 py-0.5`}>
                        {s.environment}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <StatusDot status={s.status} />
                        <span className="text-xs capitalize">{s.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-xs">
                      <span className={s.avgLatencyMs > 500 ? "text-orange-400" : s.avgLatencyMs > 200 ? "text-yellow-400" : "text-foreground"}>
                        {s.avgLatencyMs}ms
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-xs">
                      <span className={s.errorRate > 0.1 ? "text-red-400" : s.errorRate > 0.05 ? "text-orange-400" : "text-foreground"}>
                        {(s.errorRate * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-xs">
                      <span className={s.anomalyRate > 0.4 ? "text-red-400" : s.anomalyRate > 0.2 ? "text-yellow-400" : "text-foreground"}>
                        {(s.anomalyRate * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-xs text-foreground">{s.requestPerMin.toLocaleString()}</td>
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
