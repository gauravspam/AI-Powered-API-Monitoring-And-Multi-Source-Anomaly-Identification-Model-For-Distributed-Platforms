# API Monitoring Backend Service - Setup & API Reference Guide

## Overview

This is the Spring Boot backend for the AI-Powered API Monitoring and Anomaly Detection system. It provides REST APIs for ingesting metrics, logs, and traces from distributed services, stores them in PostgreSQL, and integrates with a Python ML service for anomaly detection.

**Base URL:** `http://localhost:8080`

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Starting the Backend](#starting-the-backend)
3. [Starting PostgreSQL](#starting-postgresql)
4. [API Endpoints](#api-endpoints)
5. [Request/Response Examples](#requestresponse-examples)
6. [Configuration](#configuration)
7. [Database Schema](#database-schema)
8. [Building & Running](#building--running)
9. [Testing with curl](#testing-with-curl)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Java | 17+ | Required for Spring Boot 3.x |
| PostgreSQL | 15+ | Runs on port 5433 (Docker maps 5432→5433) |
| Gradle | 8.x | Included via gradlew wrapper |

### Database Credentials

| Property | Value |
|----------|-------|
| Database | `api_monitoring` |
| Username | `api_monitor` |
| Password | `api_monitor_pwd` |

---

## Starting the Backend

### Step 1: Ensure PostgreSQL is Running

```powershell
docker ps -a | findstr postgres
```

If not running, start it:

```powershell
docker run -d --name postgres-api-monitor -e POSTGRES_DB=api_monitoring -e POSTGRES_USER=api_monitor -e POSTGRES_PASSWORD=api_monitor_pwd -p 5433:5432 postgres:15
```

### Step 2: Start the Backend

```powershell
cd backend-service
.\gradlew bootRun
```

The backend will start on **http://localhost:8080**

You should see output like:
```
Tomcat started on port 8080 (http)
Started ApiMonitoringBackendApplication in X.XXX seconds
```

---

## Starting PostgreSQL

### Option A: Docker (Recommended)

```bash
# Create and start PostgreSQL container
docker run -d `
  --name postgres-api-monitor `
  -e POSTGRES_DB=api_monitoring `
  -e POSTGRES_USER=api_monitor `
  -e POSTGRES_PASSWORD=api_monitor_pwd `
  -p 5433:5432 `
  postgres:15
```

### Option B: Docker Compose

```bash
cd infrastructure/docker
docker-compose up -d postgres
```

### Verify Connection

```powershell
# Check if PostgreSQL is accepting connections
docker logs postgres-api-monitor

# Test connection from backend (automatic on startup)
# If tables don't exist, Hibernate will create them via ddl-auto: update
```

---

## API Endpoints

### 1. Health Check Endpoints

Used to verify the service is running and healthy.

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/health` | Basic health check | `{"status": "UP", "service": "api-monitoring-backend"}` |
| GET | `/actuator/health` | Spring Actuator health | Detailed health with DB status |

**Example:**
```bash
curl http://localhost:8080/health
# Response: {"status":"UP","service":"api-monitoring-backend"}
```

---

### 2. Metrics Endpoints (`/api/metrics`)

Used to ingest and retrieve API performance metrics (CPU, memory, response time, error rate, etc.).

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|-------------|
| POST | `/api/metrics` | Ingest a single metric | - |
| POST | `/api/metrics/batch` | Ingest multiple metrics | - |
| GET | `/api/metrics/recent` | Get recent metrics | `limit` (default: 100) |
| GET | `/api/metrics/traffic` | Get traffic data | `limit` (default: 50) |
| GET | `/api/metrics/api/{apiId}` | Get metrics by API ID | `apiId` (path) |

#### POST /api/metrics - Request Body

```json
{
  "apiId": 1,
  "serviceName": "user-service",
  "cpuUsage": 45.2,
  "memoryUsage": 62.8,
  "diskIoBytes": 1024000,
  "networkIoBytes": 512000,
  "responseTimeMs": 125,
  "requestCount": 1500,
  "errorRate": 0.02,
  "timestamp": "2026-04-11T10:30:00"
}
```

#### POST /api/metrics - Response

```json
{
  "status": "success",
  "message": "Metric saved successfully",
  "id": 123,
  "timestamp": "2026-04-11T10:30:00"
}
```

#### GET /api/metrics/recent?limit=10 - Response

```json
[
  {
    "id": 123,
    "apiLogId": 1,
    "serviceName": "user-service",
    "cpuUsagePercent": 45.2,
    "memoryUsagePercent": 62.8,
    "diskIoBytes": 1024000,
    "networkIoBytes": 512000,
    "responseTimeMs": 125,
    "requestCount": 1500,
    "errorRate": 0.02,
    "metricTimestamp": "2026-04-11T10:30",
    "createdAt": "2026-04-11T10:30:00"
  }
]
```

---

### 3. Logs Endpoints (`/api/logs`)

Used to ingest and search application logs (typically forwarded via Fluentd to OpenSearch).

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|-------------|
| POST | `/api/logs` | Ingest a log entry | - |
| POST | `/api/logs/batch` | Ingest multiple logs | - |
| GET | `/api/logs/recent` | Get recent logs | `limit` (default: 100) |
| GET | `/api/logs/search` | Search logs | `query`, `limit` |
| GET | `/api/logs/service/{serviceName}` | Get logs by service | `serviceName`, `limit` |
| GET | `/api/logs/level/{level}` | Get logs by level | `level` (INFO, ERROR, WARN), `limit` |
| GET | `/api/logs/events` | Get log events | `limit` |
| GET | `/api/logs/streams` | Get log streams | `limit` |

#### POST /api/logs - Request Body

```json
{
  "serviceName": "user-service",
  "level": "INFO",
  "message": "User login successful",
  "environment": "production",
  "timestamp": "2026-04-11T10:30:00Z"
}
```

#### GET /api/logs/search?query=error&limit=5 - Response

```json
[
  {
    "id": "log-123",
    "serviceName": "payment-service",
    "level": "ERROR",
    "message": "Payment processing failed: timeout",
    "environment": "production",
    "timestamp": "2026-04-11T10:28:00Z"
  }
]
```

---

### 4. Traces Endpoints (`/api/traces`)

Used to ingest and retrieve distributed tracing data (OpenTelemetry-compatible).

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|-------------|
| POST | `/api/traces/ingest` | Ingest a trace | - |
| POST | `/api/traces/ingest/batch` | Ingest multiple traces | - |
| GET | `/api/traces/recent` | Get recent traces | `page`, `size` |
| GET | `/api/traces/service/{serviceName}` | Get traces by service | `serviceName`, `page`, `size` |
| GET | `/api/traces/search` | Search traces | `serviceName`, `startTime`, `endTime`, `page`, `size` |
| GET | `/api/traces/stats/{serviceName}` | Get service statistics | `serviceName` |
| GET | `/api/traces/{traceId}` | Get trace by ID | `traceId` |

#### POST /api/traces/ingest - Request Body

```json
{
  "traceId": "abc-123-def",
  "spanId": "span-456",
  "parentSpanId": "span-789",
  "serviceName": "payment-service",
  "operationName": "POST /payment/process",
  "duration": 250,
  "statusCode": 200,
  "timestamp": "2026-04-11T10:30:00Z",
  "tags": {
    "http.method": "POST",
    "endpoint": "/payment/process",
    "database.query": "SELECT * FROM payments"
  }
}
```

#### POST /api/traces/ingest - Response

```json
{
  "id": 456,
  "traceId": "abc-123-def",
  "status": "success",
  "message": "Trace ingested successfully"
}
```

#### GET /api/traces/stats/payment-service - Response

```json
{
  "serviceName": "payment-service",
  "totalTraces": 1250,
  "averageDurationMs": 185.5
}
```

---

### 5. Anomalies Endpoints (`/api/anomalies`)

Used to analyze logs for anomalies and retrieve detected anomalies. Integrates with Python ML service for anomaly detection.

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|-------------|
| POST | `/api/anomalies/analyze` | Analyze a log for anomalies | - |
| GET | `/api/anomalies/recent` | Get recent anomalies | `limit` (default: 10) |
| GET | `/api/anomalies/severity/{severity}` | Get by severity | `severity` (HIGH, MEDIUM, LOW) |
| GET | `/api/anomalies/critical` | Get critical anomalies | `limit` |
| GET | `/api/anomalies/unacknowledged` | Get unacknowledged anomalies | - |
| POST | `/api/anomalies/{id}/acknowledge` | Acknowledge an anomaly | `id` (path), optional `username` |
| POST | `/api/anomalies/{id}/resolve` | Resolve an anomaly | `id` (path) |
| GET | `/api/anomalies/stats` | Get anomaly statistics | `apiName` |

#### POST /api/anomalies/analyze - Request Body

```json
{
  "apiName": "user-service",
  "endpoint": "/api/users",
  "method": "POST",
  "statusCode": 500,
  "responseTime": 5200,
  "errorMessage": "Connection timeout",
  "timestamp": "2026-04-11T10:30:00"
}
```

#### POST /api/anomalies/analyze - Response

```json
{
  "id": 89,
  "apiName": "user-service",
  "severity": "HIGH",
  "hybridEnsembleScore": 0.92,
  "isolationForestScore": 0.88,
  "lstmScore": 0.85,
  "autoencoderScore": 0.78,
  "status": "ACTIVE",
  "detectedAt": "2026-04-11T10:30:00",
  "description": "High error rate detected with response time anomaly"
}
```

#### GET /api/anomalies/recent?limit=5 - Response

```json
[
  {
    "id": 89,
    "apiName": "user-service",
    "endpoint": "/api/users",
    "severity": "HIGH",
    "hybridEnsembleScore": 0.92,
    "status": "ACTIVE",
    "detectedAt": "2026-04-11T10:30:00"
  },
  {
    "id": 88,
    "apiName": "payment-service",
    "endpoint": "/payment/checkout",
    "severity": "MEDIUM",
    "hybridEnsembleScore": 0.71,
    "status": "ACKNOWLEDGED",
    "detectedAt": "2026-04-11T10:25:00"
  }
]
```

---

### 6. Alerts Endpoints (`/api/alerts`)

Used to manage alerts (synonym for anomalies in this system).

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|-------------|
| GET | `/api/alerts` | Get all alerts | `limit` (default: 50) |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert | `id` (path) |
| POST | `/api/alerts/{id}/resolve` | Resolve an alert | `id` (path) |

---

### 7. Overview & Dashboard Endpoints

Used to get dashboard data and service overviews.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/overview` | Get dashboard overview with metrics summaries |
| GET | `/api/overview/environment-summary` | Get environment summary |
| GET | `/api/services` | Get all monitored services |
| GET | `/api/dashboard/anomalies` | Get anomalies for dashboard |
| GET | `/api/models` | Get ML models info |

#### GET /api/overview - Response

```json
{
  "totalServices": 12,
  "totalMetrics": 15420,
  "totalLogs": 8950,
  "totalTraces": 4520,
  "totalAnomalies": 23,
  "activeAnomalies": 5,
  "services здоровых": 10,
  "services в деградации": 2,
  "services недоступны": 0
}
```

#### GET /api/services - Response

```json
[
  {
    "id": 1,
    "name": "api-gateway",
    "ownerTeam": "Platform Team",
    "environment": "production",
    "status": "healthy",
    "avgLatencyMs": 45,
    "errorRate": 0.02,
    "anomalyRate": 0.1,
    "lastDeploymentAt": "2026-04-06T10:00:00",
    "requestPerMin": 1200,
    "tags": ["api", "gateway"]
  }
]
```

#### GET /api/models - Response

```json
[
  {
    "id": 1,
    "name": "MSIF-LSTM",
    "version": "1.0.0",
    "type": "LSTM",
    "status": "online",
    "latencyMs": 45,
    "throughputPerSec": 220,
    "accuracy": 94.2,
    "lastRetrainAt": "2026-04-08T10:00:00"
  }
]
```

---

## Request/Response Examples

### Complete Workflow Example

#### Step 1: Ingest a Metric

```bash
curl -X POST http://localhost:8080/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "apiId": 1,
    "serviceName": "user-service",
    "cpuUsage": 45.2,
    "memoryUsage": 62.8,
    "responseTimeMs": 125,
    "requestCount": 1500,
    "errorRate": 0.02
  }'
```

#### Step 2: Check Recent Metrics

```bash
curl http://localhost:8080/api/metrics/recent?limit=5
```

#### Step 3: Analyze for Anomalies

```bash
curl -X POST http://localhost:8080/api/anomalies/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "apiName": "user-service",
    "endpoint": "/api/users",
    "method": "POST",
    "statusCode": 500,
    "responseTime": 5200,
    "errorMessage": "Connection timeout"
  }'
```

#### Step 4: Get Overview

```bash
curl http://localhost:8080/api/overview
```

---

## Configuration

### Main Configuration File

`src/main/resources/application.yml`

```yaml
spring:
  application:
    name: api-monitoring-backend
    version: 1.0.0

  datasource:
    url: jdbc:postgresql://localhost:5433/api_monitoring?timezone=Asia/Kolkata
    username: api_monitor
    password: api_monitor_pwd
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
      connection-timeout: 30000

  jpa:
    hibernate:
      ddl-auto: update  # Creates missing tables, safe (no data loss)
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
    show-sql: false

server:
  port: 8080

# Python ML Service
python:
  service:
    url: http://localhost:9000
    enabled: true
    timeout: 30

# Fluentd (log forwarding)
fluentd:
  enabled: true
  host: localhost
  port: 24224
```

### Key Settings Explained

| Setting | Default | Description |
|---------|---------|-------------|
| `server.port` | 8080 | HTTP listener port |
| `spring.datasource.url` | - | PostgreSQL JDBC URL |
| `spring.jpa.hibernate.ddl-auto` | update | Table auto-creation mode |
| `python.service.url` | http://localhost:9000 | ML service endpoint |
| `python.service.enabled` | true | Enable ML integration |
| `fluentd.enabled` | true | Enable Fluentd log forwarding |
| `opensearch.enabled` | false | Enable OpenSearch (optional) |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ML_SERVICE_URL` | Python ML service URL | http://localhost:9000 |
| `ML_SERVICE_ENABLED` | Enable ML service | true |
| `SPRING_PROFILES_ACTIVE` | Spring profile | default |
| `POSTGRES_HOST` | Database host | localhost |
| `POSTGRES_PORT` | Database port | 5433 |

---

## Database Schema

### Tables (auto-created by Hibernate)

The backend automatically creates these tables in PostgreSQL via Hibernate's `ddl-auto: update`.

| Table | Entity | Description |
|-------|--------|-------------|
| `metric_record` | MetricRecord | API performance metrics |
| `log_record` | LogRecord | Application logs |
| `trace_record` | TraceRecord | Distributed traces |
| `anomaly_record` | AnomalyRecord | Detected anomalies |
| `alert_record` | AlertRecord | Alert records |
| `system_metrics` | SystemMetrics | System-level metrics |

### metric_record Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT | Primary key, auto-generated |
| `api_log_id` | BIGINT | Foreign key to log |
| `service_name` | VARCHAR(255) | Service name |
| `cpu_usage_percent` | DOUBLE | CPU usage % |
| `memory_usage_percent` | DOUBLE | Memory usage % |
| `disk_io_bytes` | BIGINT | Disk I/O bytes |
| `network_io_bytes` | BIGINT | Network I/O bytes |
| `response_time_ms` | BIGINT | Response time in ms |
| `request_count` | BIGINT | Request count |
| `error_rate` | DOUBLE | Error rate (0-1) |
| `metric_timestamp` | TIMESTAMP | Metric timestamp |
| `created_at` | TIMESTAMP | Record creation time |

### anomaly_record Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT | Primary key |
| `service_name` | VARCHAR(255) | Service name |
| `endpoint` | VARCHAR(500) | API endpoint |
| `severity` | VARCHAR(20) | HIGH, MEDIUM, LOW |
| `hybrid_ensemble_score` | DOUBLE | Ensemble model score |
| `isolation_forest_score` | DOUBLE | Isolation Forest score |
| `lstm_score` | DOUBLE | LSTM model score |
| `autoencoder_score` | DOUBLE | Autoencoder score |
| `status` | VARCHAR(20) | ACTIVE, ACKNOWLEDGED, RESOLVED |
| `detected_at` | TIMESTAMP | Detection time |

---

## Building & Running

### Build the Project

```powershell
.\gradlew build
```

### Run in Development

```powershell
.\gradlew bootRun
```

### Run with Specific Profile

```powershell
# Use Docker profile (reads environment variables)
.\gradlew bootRun --args="--spring.profiles.active=docker"
```

### Clean and Rebuild

```powershell
.\gradlew clean build
```

### Run Tests

```powershell
.\gradlew test
```

---

## Testing with curl

```bash
# 1. Health check
curl http://localhost:8080/health

# 2. Get recent metrics
curl http://localhost:8080/api/metrics/recent?limit=10

# 3. Get traffic data
curl http://localhost:8080/api/metrics/traffic?limit=50

# 4. Search logs
curl "http://localhost:8080/api/logs/search?query=error&limit=10"

# 5. Get recent traces
curl http://localhost:8080/api/traces/recent?page=0&size=10

# 6. Get service statistics
curl http://localhost:8080/api/traces/stats/user-service

# 7. Get recent anomalies
curl http://localhost:8080/api/anomalies/recent?limit=10

# 8. Get critical anomalies
curl http://localhost:8080/api/anomalies/critical?limit=5

# 9. Get all services
curl http://localhost:8080/api/services

# 10. Get dashboard overview
curl http://localhost:8080/api/overview

# 11. Get ML models info
curl http://localhost:8080/api/models
```

---

## Troubleshooting

### Issue: Port 8080 Already in Use

**Error:**
```
Port 8080 was already in use
```

**Solution:**
```powershell
# Find the process using port 8080
netstat -ano | findstr 8080

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change the port in application.yml
# server.port: 8081
```

### Issue: PostgreSQL Connection Refused

**Error:**
```
org.postgresql.util.PSQLException: Connection refused
```

**Solution:**
```powershell
# Check if PostgreSQL container is running
docker ps | findstr postgres

# Start the container
docker start postgres-api-monitor

# Or recreate if needed
docker rm postgres-api-monitor
docker run -d --name postgres-api-monitor -e POSTGRES_DB=api_monitoring -e POSTGRES_USER=api_monitor -e POSTGRES_PASSWORD=api_monitor_pwd -p 5433:5432 postgres:15
```

### Issue: Tables Not Created

**Error:**
```
relation "metric_record" does not exist
```

**Solution:**
1. Verify `ddl-auto: update` is set in application.yml
2. Restart the backend - Hibernate will create missing tables
3. Check PostgreSQL connection is working

### Issue: Timezone Error

**Error:**
```
FATAL: invalid value for parameter "TimeZone": "Asia/Calcutta"
```

**Solution:**
- PostgreSQL renamed "Asia/Calcutta" to "Asia/Kolkata" in 2001
- The JDBC URL already includes `timezone=Asia/Kolkata`
- If still failing, add JVM property in build.gradle:
```groovy
bootRun {
    systemProperty 'user.timezone', 'UTC'
}
```

### Issue: ML Service Not Available

**Error:**
```
ML service request failed
```

**Solution:**
```powershell
# Check if ML service is running
curl http://localhost:9000/health

# Start ML service if not running
cd ml-service/api
pip install -r requirements.txt
python app_multimodal.py

# Or disable ML service in application.yml
python:
  service:
    enabled: false
```

### Issue: CORS Errors in Frontend

**Error:**
```
Access to fetch at 'http://localhost:8080/api/...' has been blocked by CORS policy
```

**Solution:**
- Backend already has CORS configured in CorsConfig.java
- Ensure frontend is calling correct port (8080)
- Check VITE_API_URL in frontend/.env

---

## Related Files

| File | Description |
|------|-------------|
| `src/main/resources/application.yml` | Main configuration |
| `src/main/java/.../ApiMonitoringBackendApplication.java` | Main class |
| `src/main/java/.../controller/*.java` | REST controllers |
| `src/main/java/.../service/*.java` | Business logic |
| `src/main/java/.../repository/*.java` | Data access |
| `src/main/java/.../model/*.java` | Entity models |
| `src/main/java/.../dto/*.java` | Data transfer objects |
| `src/main/resources/logback-spring.xml` | Logging config |