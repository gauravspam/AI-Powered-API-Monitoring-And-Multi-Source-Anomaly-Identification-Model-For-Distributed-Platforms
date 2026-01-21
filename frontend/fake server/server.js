const express = require("express");
const cors = require("cors");
const cookieParser = require("cookie-parser");
const app = express();
const port = 8080;

// Mock data
const users = [
    { id: "1", email: "admin@example.com", password: "admin123", name: "Admin", role: "admin" },
    { id: "2", email: "user@example.com", password: "user123", name: "User", role: "user" }
];

let settingsConfig = {
    alerting: {
        slackEnabled: true,
        slackWebhook: "https://hooks.slack.com/services/...",
        pagerDutyEnabled: false,
        pagerDutyKey: "",
    },
    thresholds: {
        onPrem: 0.75,
        aws: 0.75,
        gcp: 0.75,
        azure: 0.75,
        multiCloud: 0.75,
    }
}

const mockData = {
    kpiCards: require("./data/mockDashboard").kpiCards,
    environmentSummary: require("./data/mockDashboard").environmentSummary,
    recentAnomalies: require("./data/mockDashboard").recentAnomalies,
    trafficSeries: require("./data/mockDashboard").trafficSeries,
    alerts: require("./data/mockAlerts").alerts,
    logStreams: require("./data/mockLogs").logStreams,
    logEvents: require("./data/mockLogs").logEvents,
    models: require("./data/mockModels").models,
    services: require("./data/mockServices").services
};

// In-memory storage
const sessions = new Map();

// Simple token functions
const generateToken = (userId) => Buffer.from(JSON.stringify({ userId, exp: Date.now() + 24 * 60 * 60 * 1000 })).toString("base64");
const verifyToken = (token) => {
    try {
        const payload = JSON.parse(Buffer.from(token, "base64").toString());
        return payload.exp > Date.now() ? payload : null;
    } catch {
        return null;
    }
};

// Middleware
app.use(cors({ origin: "http://localhost:5173", credentials: true }));
app.use(express.json());
app.use(cookieParser());

const authenticate = (req, res, next) => {
    const token = req.cookies.authToken;
    if (!token) return res.status(401).json({ error: "No token" });

    const payload = verifyToken(token);
    if (!payload) return res.status(401).json({ error: "Invalid token" });

    const session = sessions.get(payload.userId);
    if (!session) return res.status(401).json({ error: "No session" });

    req.user = session.user;
    next();
};

// Public endpoints
app.get("/health", (req, res) => res.send("OK"));
app.get("/api/auth/csrf", (req, res) => {
    const csrf = Buffer.from(Math.random().toString()).toString("base64").slice(0, 32);
    res.cookie("XSRF-TOKEN", csrf, { httpOnly: false, maxAge: 15 * 60 * 1000 });
    res.json({ csrfToken: csrf });
});

app.post("/api/auth/login", (req, res) => {
    const { email, password } = req.body;
    const user = users.find(u => u.email === email && u.password === password);

    if (!user) return res.status(401).json({ error: "Invalid credentials" });

    const sessionId = `session_${Date.now()}`;
    sessions.set(sessionId, { user });

    const token = generateToken(sessionId);
    res.cookie("authToken", token, { httpOnly: true, maxAge: 24 * 60 * 60 * 1000 });
    res.json({ success: true, user: user });
});

app.post("/api/auth/logout", authenticate, (req, res) => {
    sessions.delete(req.user.id);
    res.clearCookie("authToken").json({ success: true });
});

app.get("/api/auth/me", authenticate, (req, res) => {
    res.json({ success: true, user: req.user });
});

// Protected endpoints
app.get("/api/dashboard/kpi", authenticate, (req, res) => res.json(mockData.kpiCards));
app.get("/api/dashboard/env-summary", authenticate, (req, res) => res.json(mockData.environmentSummary));
app.get("/api/dashboard/anomalies", authenticate, (req, res) => res.json(mockData.recentAnomalies));
app.get("/api/dashboard/traffic", authenticate, (req, res) => res.json(mockData.trafficSeries));

app.get("/api/alerts", authenticate, (req, res) => res.json(mockData.alerts));
app.post("/api/alerts/:id/acknowledge", authenticate, (req, res) => res.json({ success: true }));

app.get("/api/logs/streams", authenticate, (req, res) => res.json(mockData.logStreams));
app.get("/api/logs/events", authenticate, (req, res) => res.json(mockData.logEvents));

app.get("/api/models", authenticate, (req, res) => res.json(mockData.models));
app.get("/api/services", authenticate, (req, res) => res.json(mockData.services));


// Adding mock API for getting current configuration
app.get("/api/settings/configuration", authenticate, (req, res) => {
    res.json(settingsConfig);
});

// Adding mock API for updating alerting and thresholds
app.post("/api/settings/update", authenticate, (req, res) => {
    
    Object.assign(settingsConfig.alerting, req.body.alerting)
    Object.assign(settingsConfig.thresholds, req.body.thresholds)

    res.json({ success: true });
});

app.listen(port, () => {
    console.log(`Server running: http://localhost:${port}`);
    console.log("Login: admin@example.com / admin123");
});
