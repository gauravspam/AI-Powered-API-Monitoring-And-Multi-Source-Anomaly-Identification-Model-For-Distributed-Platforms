import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useState } from "react";
import { CheckCircle, XCircle, Filter, RefreshCw } from "lucide-react";
import { SeverityBadge, ScoreBar, LoadingRows, EmptyState, timeAgo } from "@/components/shared/SeverityBadge";
import { useToast } from "@/hooks/use-toast";

type Anomaly = {
  id: number;
  apiName: string;
  endpoint: string;
  severity: string;
  hybridEnsembleScore: number;
  msifLstmScore: number;
  pleGruScore: number;
  status: string;
  detectedAt: string;
  isAcknowledged: boolean;
  isResolved: boolean;
  environment: string;
};

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8080";

export default function AlertsPage() {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: anomalies, isLoading, refetch } = useQuery<Anomaly[]>({
    queryKey: ["/api/proxy/alerts"],
    queryFn: () => apiRequest("GET", "/api/proxy/alerts").then(r => r.json()),
    refetchInterval: 15000,
  });

  const acknowledge = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`${BACKEND_URL}/api/anomalies/${id}/acknowledge`, { method: "POST" });
      if (!res.ok) throw new Error("Failed — backend may be offline");
      return res.json();
    },
    onSuccess: () => {
      toast({ title: "Acknowledged", description: "Anomaly marked as acknowledged." });
      qc.invalidateQueries({ queryKey: ["/api/proxy/alerts"] });
    },
    onError: (e: Error) => toast({ title: "Action Failed", description: e.message, variant: "destructive" }),
  });

  const resolve = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`${BACKEND_URL}/api/anomalies/${id}/resolve`, { method: "POST" });
      if (!res.ok) throw new Error("Failed — backend may be offline");
      return res.json();
    },
    onSuccess: () => {
      toast({ title: "Resolved", description: "Anomaly marked as resolved." });
      qc.invalidateQueries({ queryKey: ["/api/proxy/alerts"] });
    },
    onError: (e: Error) => toast({ title: "Action Failed", description: e.message, variant: "destructive" }),
  });

  const filtered = (anomalies || []).filter(a => {
    const matchSev = severityFilter === "all" || a.severity === severityFilter;
    const matchStat = statusFilter === "all" || a.status === statusFilter;
    return matchSev && matchStat;
  });

  const counts = {
    CRITICAL: (anomalies || []).filter(a => a.severity === "CRITICAL").length,
    HIGH: (anomalies || []).filter(a => a.severity === "HIGH").length,
    ACTIVE: (anomalies || []).filter(a => a.status === "ACTIVE").length,
    ACKNOWLEDGED: (anomalies || []).filter(a => a.status === "ACKNOWLEDGED").length,
  };

  return (
    <div className="space-y-4">
      {/* Summary chips */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Critical", value: counts.CRITICAL, cls: "text-red-400" },
          { label: "High", value: counts.HIGH, cls: "text-orange-400" },
          { label: "Active", value: counts.ACTIVE, cls: "text-red-400" },
          { label: "Acknowledged", value: counts.ACKNOWLEDGED, cls: "text-yellow-400" },
        ].map(({ label, value, cls }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-3 text-center">
            <div className={`text-2xl font-bold tabular-nums ${cls}`}>{value}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Filter size={13} className="text-muted-foreground" />
        <div className="flex gap-1">
          {["all", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map(s => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                severityFilter === s ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
              data-testid={`button-severity-${s}`}
            >
              {s === "all" ? "All" : s}
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          {["all", "ACTIVE", "ACKNOWLEDGED", "RESOLVED"].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                statusFilter === s ? "bg-secondary text-secondary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
              data-testid={`button-status-${s}`}
            >
              {s === "all" ? "All Status" : s}
            </button>
          ))}
        </div>
        <button
          onClick={() => refetch()}
          className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          data-testid="button-refresh-alerts"
        >
          <RefreshCw size={12} />
          Refresh
        </button>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto sticky-thead">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground">
                <th className="text-left px-4 py-2.5 font-medium">ID</th>
                <th className="text-left px-4 py-2.5 font-medium">Service</th>
                <th className="text-left px-4 py-2.5 font-medium">Endpoint</th>
                <th className="text-left px-4 py-2.5 font-medium">Severity</th>
                <th className="text-left px-4 py-2.5 font-medium">Hybrid Score</th>
                <th className="text-left px-4 py-2.5 font-medium">MSIF-LSTM</th>
                <th className="text-left px-4 py-2.5 font-medium">PLE-GRU</th>
                <th className="text-left px-4 py-2.5 font-medium">Status</th>
                <th className="text-left px-4 py-2.5 font-medium">Detected</th>
                <th className="text-left px-4 py-2.5 font-medium">Env</th>
                <th className="text-right px-4 py-2.5 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <LoadingRows cols={11} rows={8} />
              ) : filtered.length === 0 ? (
                <tr><td colSpan={11}><EmptyState message="No anomalies match filters" /></td></tr>
              ) : (
                filtered.map((a) => (
                  <tr
                    key={a.id}
                    className={`hover:bg-muted/40 transition-colors ${
                      a.severity === "CRITICAL" ? "card-critical" : a.severity === "HIGH" ? "card-high" : ""
                    }`}
                    data-testid={`row-alert-${a.id}`}
                  >
                    <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums">#{a.id}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-primary">{a.apiName}</td>
                    <td className="px-4 py-2.5 text-muted-foreground font-mono text-xs truncate max-w-[140px]">{a.endpoint}</td>
                    <td className="px-4 py-2.5"><SeverityBadge severity={a.severity} /></td>
                    <td className="px-4 py-2.5 w-32"><ScoreBar score={a.hybridEnsembleScore || 0} /></td>
                    <td className="px-4 py-2.5 text-xs tabular-nums text-muted-foreground">{(a.msifLstmScore || 0).toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-xs tabular-nums text-muted-foreground">{(a.pleGruScore || 0).toFixed(3)}</td>
                    <td className="px-4 py-2.5"><SeverityBadge severity={a.status} /></td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums whitespace-nowrap">{timeAgo(a.detectedAt)}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-xs rounded px-1.5 py-0.5 ${a.environment === "production" ? "badge-info" : "badge-normal"}`}>
                        {a.environment}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {!a.isAcknowledged && !a.isResolved && (
                          <button
                            onClick={() => acknowledge.mutate(a.id)}
                            className="flex items-center gap-1 text-xs text-yellow-400 hover:text-yellow-300 transition-colors disabled:opacity-50"
                            disabled={acknowledge.isPending}
                            data-testid={`button-acknowledge-${a.id}`}
                            title="Acknowledge"
                          >
                            <CheckCircle size={13} />
                            Ack
                          </button>
                        )}
                        {!a.isResolved && (
                          <button
                            onClick={() => resolve.mutate(a.id)}
                            className="flex items-center gap-1 text-xs text-green-400 hover:text-green-300 transition-colors disabled:opacity-50"
                            disabled={resolve.isPending}
                            data-testid={`button-resolve-${a.id}`}
                            title="Resolve"
                          >
                            <XCircle size={13} />
                            Resolve
                          </button>
                        )}
                        {a.isResolved && <span className="text-xs text-muted-foreground">Closed</span>}
                      </div>
                    </td>
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
