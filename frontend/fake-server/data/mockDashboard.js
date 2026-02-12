module.exports = {
    kpiCards: [
        { title: "Total Requests", value: "1.2M", change: 12.5, trend: "up" },
        { title: "Avg Latency", value: "45ms", change: -5.2, trend: "down" },
        { title: "Error Rate", value: "0.12%", change: 0.02, trend: "up" },
        { title: "Active Services", value: "14", change: 0, trend: "neutral" }
    ],
    environmentSummary: {
        totalServices: 14,
        healthyServices: 12,
        degradedServices: 2,
        deployments24h: 5
    },
    recentAnomalies: [
        { id: 1, service: "Auth Service", type: "Latency Spike", severity: "High", timestamp: new Date().toISOString() },
        { id: 2, service: "Payment API", type: "Error Rate", severity: "Medium", timestamp: new Date().toISOString() }
    ],
    trafficSeries: [
        { time: "10:00", value: 400 },
        { time: "11:00", value: 650 },
        { time: "12:00", value: 900 },
        { time: "13:00", value: 850 }
    ]
};
