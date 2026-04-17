# Backend Documentation

## Overview

The backend is a Spring Boot 3.x REST API service that provides data for the frontend monitoring dashboard. It collects metrics, logs, traces, and anomalies from distributed services, and integrates with the ML service for anomaly detection.

**Tech Stack:**
- Java 17+
- Spring Boot 3.x
- Spring Data JPA
- OpenSearch (for logs)
- MySQL/PostgreSQL (for persistence)

**Port:** `8080`

---

## Quick Start

```bash
cd backend-service
./mvnw spring-boot:run
```

---

## Project Structure

```
backend-service/
├── src/main/java/com/api/monitoring/backend/
│   ├── controller/          # REST API endpoints
│   ├── service/             # Business logic
│   ├── repository/           # Data access
│   ├── model/                # Entity classes
│   ├── dto/                  # Data transfer objects
│   ├── config/               # Configuration classes
│   └── util/                 # Utilities
├── src/main/resources/
│   └── application.yml       # App configuration
└── pom.xml
```

---

## API Endpoints

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/overview` | Dashboard overview stats |
| GET | `/api/dashboard/kpi` | KPI metrics |
| GET | `/api/dashboard/traffic` | Traffic chart data |
| GET | `/api/dashboard/env-summary` | Environment summary |

### Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/services` | List of services |
| GET | `/api/services/{id}` | Service details |

### Anomalies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/anomalies` | Anomaly list |
| GET | `/api/anomalies/recent` | Recent anomalies |
| POST | `/api/anomalies/{id}/acknowledge` | Acknowledge |
| POST | `/api/anomalies/{id}/resolve` | Resolve |

### Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/logs/recent` | Recent log entries |
| POST | `/api/logs/ingest` | Ingest log |

### Traces

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/traces/recent` | Recent traces |
| POST | `/api/traces/ingest` | Ingest trace |

### Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/traffic` | Traffic metrics |
| POST | `/api/metrics/ingest` | Ingest metric |

### ML Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models` | Model status |
| POST | `/api/prediction/analyze` | Get anomaly prediction |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/health` | Detailed health |

---

## Controllers

| Controller | Purpose |
|------------|---------|
| `DashboardController` | Overview, KPI, traffic data |
| `ServicesController` | Service management |
| `AnomalyController` | Anomaly CRUD operations |
| `AlertsController` | Alert management |
| `LogsController` | Log retrieval |
| `TracesController` | Trace retrieval |
| `MetricsController` | Metrics data |
| `ModelsController` | ML model status |
| `PredictionController` | ML predictions |
| `HealthController` | Health checks |

---

## Services

| Service | Purpose |
|---------|---------|
| `DashboardService` | Dashboard data aggregation |
| `AnomalyService` | Anomaly detection logic |
| `OverviewService` | Overview stats |
| `MLServiceClient` | Communication with ML service |
| `OpenSearchLogService` | Log storage/retrieval |

---

## Configuration

`application.yml` key settings:

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/api_monitor
  opensearch:
    uris: http://localhost:9200

ml:
  service:
    url: http://localhost:9000
```

---

## Integration

### ML Service
The backend forwards metrics, logs, and traces to the ML service for anomaly prediction via `/predict/flexible` endpoint.

### OpenSearch
Logs are stored and queried from OpenSearch for real-time retrieval.