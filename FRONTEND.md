# Frontend Documentation

## Overview

The frontend is a React 19 + Vite 7 application providing a real-time monitoring dashboard for distributed API systems. It communicates with the backend REST API to display metrics, logs, traces, anomalies, and ML model status.

**Tech Stack:**
- React 19 with Vite 7
- Material UI (MUI) 7
- React Router 7
- TanStack Query for data fetching
- Recharts for data visualization

**Access URL:** `http://localhost:5173`

---

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── http.js              # API client (axios wrapper)
│   ├── components/
│   │   ├── SharedComponents.jsx # Reusable UI components
│   │   ├── SideNav.jsx          # Navigation sidebar
│   │   └── TopBar.jsx           # Top header bar
│   ├── contexts/
│   │   ├── AuthContext.jsx     # Authentication state
│   │   └── ThemeContext.jsx     # Dark/light theme
│   ├── data/
│   │   └── mock*.js             # Mock data for development
│   ├── layouts/
│   │   └── MainLayout.jsx       # Main layout wrapper
│   ├── pages/
│   │   ├── Dashboard.jsx        # Overview with KPIs & charts
│   │   ├── Services.jsx         # Service health grid
│   │   ├── Alerts.jsx            # Anomaly alerts list
│   │   ├── Logs.jsx             # Log entries viewer
│   │   ├── Traces.jsx           # Distributed traces
│   │   ├── Models.jsx           # ML model status
│   │   ├── Simulator.jsx        # Signal simulator for ML
│   │   ├── Settings.jsx         # App settings
│   │   └── Login.jsx            # Authentication
│   ├── theme.js                  # MUI theme configuration
│   └── App.jsx                   # Main app component
├── package.json
└── vite.config.js
```

---

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Overview with KPIs, charts, anomaly list |
| `/services` | Services | Service health grid with status |
| `/alerts` | Alerts | Anomaly alerts with severity filters |
| `/logs` | Logs | Log entries with level/service filters |
| `/traces` | Traces | Distributed traces with latency chart |
| `/models` | Models | ML model status and performance |
| `/simulator` | Simulator | Signal simulator for ML testing |
| `/settings` | Settings | App configuration |

---

## API Endpoints

The frontend expects these backend API endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /api/overview` | Dashboard overview stats |
| `GET /api/services` | List of services |
| `GET /api/anomalies` | Anomaly/alert list |
| `GET /api/logs/recent` | Recent log entries |
| `GET /api/traces/recent` | Recent traces |
| `GET /api/models` | ML model status |
| `GET /api/dashboard/kpi` | KPI metrics |
| `GET /api/dashboard/traffic` | Traffic chart data |
| `POST /api/anomalies/{id}/acknowledge` | Acknowledge anomaly |
| `POST /api/anomalies/{id}/resolve` | Resolve anomaly |

---

## Configuration

Environment variables (create `.env`):

```env
VITE_BACKEND_URL=http://localhost:8080
VITE_ML_SERVICE_URL=http://localhost:9000
```

---

## Build & Run

```bash
# Development
npm run dev

# Production build
npm run build
npm run preview

# Lint
npm run lint
```

---

## Features

- **Dark/Light Theme** - Toggle via TopBar
- **Real-time Updates** - Auto-refresh with TanStack Query
- **Mock Data** - Falls back to mock data when backend unavailable
- **Responsive Design** - Works on desktop and tablet
- **Filtering** - Service, severity, time range filters on each page