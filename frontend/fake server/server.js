const express = require("express");
const cors = require("cors");
const app = express();
const port = 8080;

// Middleware
app.use(cors());
app.use(express.json());

// Import Data from the data folder
const { kpiCards, environmentSummary, recentAnomalies, trafficSeries } = require("./data/mockDashboard");
const { alerts } = require("./data/mockAlerts");
const { logStreams, logEvents } = require("./data/mockLogs");
const { models } = require("./data/mockModels");
const { services } = require("./data/mockServices");

// Dashboard Endpoints
app.get("/api/dashboard/kpi", (req, res) => res.json(kpiCards));
app.get("/api/dashboard/env-summary", (req, res) => res.json(environmentSummary));
app.get("/api/dashboard/anomalies", (req, res) => res.json(recentAnomalies));
app.get("/api/dashboard/traffic", (req, res) => res.json(trafficSeries));

// Alerts Endpoints
app.get("/api/alerts", (req, res) => res.json(alerts));

// Logs Endpoints
app.get("/api/logs/streams", (req, res) => res.json(logStreams));
app.get("/api/logs/events", (req, res) => res.json(logEvents));

// Models Endpoints
app.get("/api/models", (req, res) => res.json(models));

// Services Endpoints
app.get("/api/services", (req, res) => res.json(services));

// Health Check
app.get("/health", (req, res) => res.status(200).send("OK"));

app.listen(port, () => {
  console.log(`🚀 Dashboard API running at http://localhost:${port}`);
});