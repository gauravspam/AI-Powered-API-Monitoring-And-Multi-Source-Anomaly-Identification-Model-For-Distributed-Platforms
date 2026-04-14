# API Monitoring Frontend - Setup & UI Reference Guide

## Overview

The Frontend is a React + Vite web application that provides a dashboard for monitoring API services, viewing logs, managing alerts, and tracking AI model performance. It communicates with the Backend REST API to display real-time data.

**Tech Stack:**
- React 19 with Vite 7
- Material UI (MUI) 7 for components
- React Router 7 for navigation
- Axios for HTTP requests

**Access URL:** `http://localhost:5173` (default Vite dev server)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Starting the Frontend](#starting-the-frontend)
3. [Project Structure](#project-structure)
4. [Pages & Routes](#pages--routes)
5. [Components](#components)
6. [API Integration](#api-integration)
7. [Configuration](#configuration)
8. [Building & Running](#building--running)
9. [Key Features](#key-features)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Node.js | 18+ | LTS recommended |
| npm | 9+ | Comes with Node.js |
| Backend | Running | On port 8080 |

### Verify Backend is Running

Before starting the frontend, ensure the backend is running:

```bash
curl http://localhost:8080/health
# Expected: {"status":"UP","service":"api-monitoring-backend"}
```

---

## Starting the Frontend

### Step 1: Install Dependencies

```powershell
cd frontend
npm install
```

### Step 2: Start Development Server

```powershell
npm run dev
```

The frontend will start at **http://localhost:5173**

### Step 3: Access in Browser

Open your browser and navigate to:
```
http://localhost:5173
```

You should see the login page. The default login credentials are typically:
- Username: `admin`
- Password: `admin`

---

## Project Structure

```
frontend/
├── public/                     # Static assets
├── src/
│   ├── api/
│   │   └── http.js            # Axios configuration
│   ├── components/            # Reusable UI components
│   │   ├── AlertList.jsx      # Alert list display
│   │   ├── AnomalyTable.jsx  # Anomaly data table
│   │   ├── EnvironmentFilter.jsx
│   │   ├── LogTimeline.jsx    # Log event timeline
│   │   ├── MetricChart.jsx   # Charts for metrics
│   │   ├── SideNav.jsx        # Side navigation
│   │   ├── StatCard.jsx       # KPI stat cards
│   │   ├── StatusChip.jsx     # Status badges
│   │   ├── TopBar.jsx         # Top navigation bar
│   │   └── ProtectedRoute.jsx # Auth protection
│   ├── contexts/
│   │   └── AuthContext.jsx    # Authentication context
│   ├── layouts/
│   │   └── MainLayout.jsx     # Main app layout
│   ├── pages/                # Page components
│   │   ├── Dashboard.jsx     # Main dashboard
│   │   ├── Services.jsx       # Services list
│   │   ├── Alerts.jsx         # Alerts management
│   │   ├── Logs.jsx           # Logs viewer
│   │   ├── Models.jsx         # AI models info
│   │   ├── Settings.jsx       # Settings page
│   │   ├── Login.jsx          # Login page
│   │   └── NotFound.jsx       # 404 page
│   ├── routes/
│   │   └── AppRoutes.jsx      # Route definitions
│   ├── App.jsx               # Root component
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles
├── package.json              # Dependencies
├── vite.config.js           # Vite configuration
└── .env                      # Environment variables
```

---

## Pages & Routes

The application uses React Router with protected routes. All routes under `/` require authentication except `/login`.

### Route Overview

| Path | Page | Description |
|------|------|-------------|
| `/login` | Login | Authentication page (public) |
| `/` | Dashboard | Main monitoring dashboard |
| `/services` | Services | Services list with metrics |
| `/alerts` | Alerts | Alert management |
| `/logs` | Logs | Log stream viewer |
| `/models` | Models | AI model information |
| `/settings` | Settings | User settings |
| `*` | NotFound | 404 page |

### 1. Dashboard (`/`)

The main landing page showing:

- **KPI Cards** - Four stat cards displaying:
  - Total Requests
  - Error Rate
  - Anomaly Rate
  - Avg Latency

- **Traffic Chart** - Line chart showing requests per second over time

- **Environment Health** - List of environments with status and uptime

- **Recent Anomalies** - Table of recent anomalies with filtering

**Features:**
- Auto-refresh every 30 seconds
- Manual refresh button
- Filter by environment and severity
- Module-level caching for performance

---

### 2. Services (`/services`)

Displays all monitored API services in a data grid:

**Columns:**
- Service Name
- Owner Team
- Environment
- Status (healthy/degraded/down)
- Avg Latency (ms)
- Error Rate (%)
- Anomaly Rate (%)
- Last Deployment
- Requests Per Minute (RPM)

**Features:**
- Search by service name
- Filter by environment
- Filter by status
- Click row to view service details
- Service detail drawer shows:
  - Owner team
  - Environment & status
  - Tags
  - Metrics
  - Recent anomalies

---

### 3. Alerts (`/alerts`)

Manages system alerts and anomalies:

**Filters:**
- Severity (All/Critical/High/Medium/Low)
- Status (All/Open/Acknowledged/Resolved)
- Environment

**Actions:**
- Acknowledge alert
- Resolve alert

**Related Logs:**
- Shows related log events for selected alert

---

### 4. Logs (`/logs`)

Log stream viewer with timeline:

**Log Ingestion Status:**
- Cards showing each log stream:
  - Service name
  - Status (active)
  - Source (fluentd)
  - Environment
  - Ingestion lag (seconds)

**Filters:**
- Environment
- Service
- Log level (INFO/WARN/ERROR)
- Search messages

**Log Timeline:**
- Visual timeline of log events
- Color-coded by level

---

### 5. Models (`/models`)

AI model information display:

**Columns:**
- Model Name
- Version
- Type (LSTM, GRU, Ensemble)
- Status (online/warming/offline)
- Latency (ms)
- Throughput/sec
- Last Retrain
- Accuracy (%)

**Filters:**
- Model Type
- Status
- Search

---

### 6. Login (`/login`)

Authentication page:

- Username input
- Password input
- Login button

After successful login, redirects to Dashboard.

---

## Components

### Layout Components

#### MainLayout.jsx
The main application shell containing:
- Side navigation (SideNav)
- Top bar (TopBar)
- Content area

#### SideNav.jsx
Left-side navigation menu with icons:
- Dashboard
- Services
- Alerts
- Logs
- Models
- Settings

#### TopBar.jsx
Top navigation bar with:
- Application title
- User info
- Logout button

---

### Data Display Components

#### StatCard.jsx
Displays a single KPI metric:
- Icon
- Label
- Value

#### AnomalyTable.jsx
DataGrid showing anomalies:
- ID
- Service Name
- Endpoint
- Severity (color-coded)
- Score
- Detected At
- Status

#### AlertList.jsx
List of alerts with:
- Alert details
- Acknowledge button
- Resolve button

#### MetricChart.jsx
Line chart using MUI Charts:
- Configurable metric keys
- Customizable height
- Title display

#### LogTimeline.jsx
Timeline view of log events:
- Timestamp
- Level (color-coded)
- Service name
- Message

#### StatusChip.jsx
Badge component for status/severity:
- healthy (green)
- degraded (yellow)
- down (red)
- high/critical (red)
- medium (yellow)
- low (green)

#### EnvironmentFilter.jsx
Dropdown for environment selection:
- All
- production
- staging
- development

---

## API Integration

### HTTP Client Configuration

File: `src/api/http.js`

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
    withCredentials: true,
});

// Request interceptor for CSRF token
api.interceptors.request.use((config) => {
    const method = config.method?.toUpperCase();
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
        const cookies = document.cookie.split(';');
        const csrfCookie = cookies.find(cookie => cookie.trim().startsWith('XSRF-TOKEN='));
        if (csrfCookie) {
            const csrfToken = decodeURIComponent(csrfCookie.split('=')[1]);
            config.headers['X-XSRF-TOKEN'] = csrfToken;
        }
    }
    return config;
}, (error) => Promise.reject(error));

export default api;
```

### API Endpoints Used

| Frontend Call | Backend Endpoint |
|---------------|-----------------|
| `api.get('/overview')` | `/api/overview` |
| `api.get('/metrics/traffic')` | `/api/metrics/traffic` |
| `api.get('/anomalies/recent')` | `/api/anomalies/recent` |
| `api.get('/services')` | `/api/services` |
| `api.get('/alerts')` | `/api/alerts` |
| `api.get('/logs/events')` | `/api/logs/events` |
| `api.get('/logs/streams')` | `/api/logs/streams` |
| `api.get('/models')` | `/api/models` |
| `api.post('/alerts/{id}/acknowledge')` | `/api/alerts/{id}/acknowledge` |
| `api.post('/alerts/{id}/resolve')` | `/api/alerts/{id}/resolve` |

---

## Configuration

### Environment Variables

Create a `.env` file in the frontend root:

```bash
# Backend API URL (required)
VITE_API_BASE_URL=http://localhost:8080/api

# Alternatively, use VITE_API_URL for just the base
VITE_API_URL=http://localhost:8080/api
```

### Vite Configuration

File: `vite.config.js`

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    react: ["react", "react-dom"],
                    router: ["react-router-dom"],
                    muiCore: ["@mui/material", "@mui/lab"],
                    muiIcons: ["@mui/icons-material"],
                    muiCharts: ["@mui/x-charts"],
                    muiDataGrid: ["@mui/x-data-grid"],
                },
            },
        },
    },
    proxy: {
        '/api': {
            target: 'http://localhost:8080',
            changeOrigin: true,
        },
    },
});
```

### Proxy Configuration

The frontend proxies API requests to the backend during development:

```javascript
proxy: {
    '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
    },
}
```

This allows calling `/api/metrics` instead of `http://localhost:8080/api/metrics` during development.

---

## Building & Running

### Development Mode

```powershell
npm run dev
```

Starts the Vite development server with hot module replacement (HMR).

### Production Build

```powershell
npm run build
```

Creates optimized production build in `dist/` folder.

### Preview Production Build

```powershell
npm run preview
```

Locally preview the production build.

### Lint Code

```powershell
npm run lint
```

Run ESLint to check code quality.

---

## Key Features

### 1. Performance Optimizations

#### Module-Level Caching
Each page stores fetched data at the module level, persisting across component unmounts/mounts:

```javascript
let cachedData = {
  services: null,
  anomalies: null,
  timestamp: null,
};
```

#### Pre-fetching on Module Load
Data is fetched as soon as the module loads, before the component mounts:

```javascript
// Start prefetching immediately when module loads
prefetchData();
```

#### Throttled Polling
Background polling is throttled to prevent excessive API calls:

```javascript
const THROTTLE_MS = 5000;  // 5 seconds
const POLL_INTERVAL_MS = 30000;  // 30 seconds
```

#### Smart Change Detection
State is only updated if data length changes:

```javascript
const shouldUpdate = newData.length !== oldData.length;
if (shouldUpdate) setData(newData);
```

---

### 2. User Experience

#### Loading States
Components show loading states during data fetch.

#### Error Handling
API errors are caught and handled gracefully with fallback data.

#### Filter Persistence
Filters are applied via memoized functions for performance.

#### Drawers & Modals
Service details shown in slide-out drawers for quick access.

#### Responsive Design
Layout adapts to different screen sizes using MUI's grid system.

---

### 3. Data Visualization

#### Line Charts
Traffic data visualized with MUI Charts line charts.

#### Data Grids
Services and models displayed in sortable, paginated data grids.

#### Status Badges
Color-coded chips for quick status identification.

#### Timeline Views
Log events shown in chronological timeline.

---

## Troubleshooting

### Issue: CORS Errors

**Error:**
```
Access to fetch at 'http://localhost:8080/api/...' has been blocked by CORS policy
```

**Solution:**
1. Ensure backend has CORS configured in `CorsConfig.java`
2. Verify VITE_API_BASE_URL is set correctly in `.env`
3. Check proxy configuration in `vite.config.js`

---

### Issue: Login Page Loops

**Error:**
Login keeps redirecting back to login page after entering credentials.

**Solution:**
1. Check AuthContext.jsx for correct authentication logic
2. Verify backend `/api/services` or another protected endpoint is accessible
3. Check cookie handling for CSRF token

---

### Issue: No Data Displayed

**Error:**
Pages show "No data available" or empty states.

**Solution:**
1. Verify backend is running: `curl http://localhost:8080/health`
2. Check browser console for API errors
3. Verify API endpoints return data: `curl http://localhost:8080/api/services`

---

### Issue: Port Already in Use

**Error:**
```
Port 5173 was already in use
```

**Solution:**
```powershell
# Find process using port 5173
netstat -ano | findstr 5173

# Kill process or change port in vite.config.js
```

---

### Issue: Proxy Not Working

**Error:**
API calls fail with "502 Bad Gateway" or "404 Not Found".

**Solution:**
1. Ensure backend is running on port 8080
2. Check proxy target in `vite.config.js`:
```javascript
proxy: {
    '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
    },
}
```

---

### Issue: Missing Environment Variables

**Error:**
Build fails or wrong API URL used.

**Solution:**
Create `.env` file in frontend root:

```bash
VITE_API_BASE_URL=http://localhost:8080/api
```

---

## Related Files

| File | Description |
|------|-------------|
| `package.json` | Dependencies and scripts |
| `vite.config.js` | Vite and proxy config |
| `.env` | Environment variables |
| `src/api/http.js` | Axios configuration |
| `src/routes/AppRoutes.jsx` | Route definitions |
| `src/contexts/AuthContext.jsx` | Authentication logic |
| `src/layouts/MainLayout.jsx` | App shell |

---

## Dependencies

### Production Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^19.2.3 | UI framework |
| react-dom | ^19.2.3 | React DOM |
| react-router-dom | ^7.11.0 | Routing |
| @mui/material | ^7.3.6 | UI components |
| @mui/lab | ^7.0.1-beta.20 | Lab components |
| @mui/icons-material | ^7.3.6 | Icons |
| @mui/x-charts | ^8.23.0 | Charts |
| @mui/x-data-grid | ^8.23.0 | Data grids |
| axios | ^1.13.2 | HTTP client |
| @emotion/react | ^11.14.0 | Styling |
| @emotion/styled | ^11.14.1 | Styling |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| vite | ^7.2.4 | Build tool |
| @vitejs/plugin-react | ^5.1.2 | React plugin |
| eslint | ^9.39.1 | Linting |
| @eslint/js | ^9.39.1 | ESLint config |

---

## Quick Reference

### Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Access URL

```
http://localhost:5173
```

### Login Credentials

```
Username: admin
Password: admin
```

### API Base URL

```
http://localhost:8080/api
```

### Key Pages

| Page | URL | Path |
|------|-----|------|
| Login | /login | Login.jsx |
| Dashboard | / | Dashboard.jsx |
| Services | /services | Services.jsx |
| Alerts | /alerts | Alerts.jsx |
| Logs | /logs | Logs.jsx |
| Models | /models | Models.jsx |
| Settings | /settings | Settings.jsx |