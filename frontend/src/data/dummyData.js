export const dashboardData = {
  kpis: {
    apis: 124,
    rps: 9200,
    errorRate: 1.8,
    anomalies: 6,
    riskScore: 0.74
  },
  recentAnomalies: [
    { api: "Order API", type: "Latency Spike", severity: "High", time: "12:01" },
    { api: "Auth API", type: "Traffic Drop", severity: "Medium", time: "11:44" }
  ]
};

export const apisData = [
  { id: 1, name: "Order API", source: "Cloud", status: "Critical", latency: 900, error: 6.1 },
  { id: 2, name: "Auth API", source: "SaaS", status: "Healthy", latency: 120, error: 0.3 },
  { id: 3, name: "User API", source: "On-Prem", status: "Degraded", latency: 350, error: 1.9 }
];

export const anomaliesData = [
  { api: "Order API", type: "Latency Spike", score: 0.92, severity: "High", time: "12:01" },
  { api: "Auth API", type: "Traffic Drop", score: 0.71, severity: "Medium", time: "11:44" }
];

export const predictionsData = [
  { api: "Order API", risk: 0.82, eta: "15 mins" },
  { api: "Payment API", risk: 0.77, eta: "25 mins" }
];

export const alertsData = [
  { name: "High Latency", api: "Order API", severity: "High", time: "12:01", status: "Open" }
];

export const systemHealthData = {
  fluentd: "Running",
  opensearch: "Healthy",
  mlService: "Online",
  alertManager: "Online",
  ingestionRate: "120k logs/sec",
  lag: "200ms"
};
