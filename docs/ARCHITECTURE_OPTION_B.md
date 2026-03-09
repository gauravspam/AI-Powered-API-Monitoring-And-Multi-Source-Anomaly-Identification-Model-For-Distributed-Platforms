# Architecture: Option B - Observability Pipeline

**Date**: March 8, 2026  
**Status**: Implemented  
**Architecture Pattern**: Hybrid Observability - Specialized pipelines for each signal type

---

## 🎯 Executive Summary

This project implements **Option B** - a pragmatic observability architecture that:
- Uses **Fluentd exclusively for logs** → OpenSearch
- Keeps **metrics and traces** flowing through **backend API endpoints** → PostgreSQL
- Maintains the existing ML/anomaly detection pipeline with minimal disruption
- Provides a clear migration path to full OpenTelemetry in the future

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                              │
│  (Backend API, Frontend, ML Service, External Services)         │
└──────────┬──────────────────────┬──────────────────────────────┘
           │                      │                      │
           │ Logs                 │ Metrics             │ Traces
           │ (JSON)               │ (JSON/REST)         │ (JSON/REST)
           ▼                      ▼                      ▼
    ┌──────────┐          ┌─────────────┐       ┌─────────────┐
    │ Fluentd  │          │  Backend    │       │  Backend    │
    │ :24224   │          │  API        │       │  API        │
    │ :9880    │          │ /api/metrics│       │ /api/traces │
    └─────┬────┘          └──────┬──────┘       └──────┬──────┘
          │                      │                      │
          │ Forward              │ HTTP POST            │ HTTP POST
          │                      │                      │
          ▼                      ▼                      ▼
    ┌──────────┐          ┌──────────────────────────────┐
    │OpenSearch│          │        PostgreSQL            │
    │  :9200   │          │  - systemmetrics table       │
    │          │          │  - distributedtraces table   │
    │ Logs     │          │  - apilogs table             │
    │ Storage  │          │  - anomalydetections table   │
    └──────────┘          └──────────┬───────────────────┘
                                     │
                                     ▼
                          ┌────────────────────┐
                          │   ML Service       │
                          │  Anomaly Detection │
                          │  Fusion Models     │
                          └────────────────────┘
```

---

## 🔄 Data Flow by Signal Type

### 1️⃣ **Logs Pipeline** (Fluentd → OpenSearch)

**Path**: Service → Fluentd → OpenSearch

**Protocols**:
- Fluentd Forward: `fluent://fluentd:24224`
- HTTP: `http://fluentd:9880/app.logs`

**Example Service Configuration** (Logback/Spring Boot):
```xml
<!-- logback-spring.xml -->
<appender name="FLUENT" class="ch.qos.logback.more.appenders.DataFluentAppender">
    <remoteHost>fluentd</remoteHost>
    <port>24224</port>
    <tag>app.backend</tag>
</appender>
```

**Fluentd Processing**:
1. Receives logs on port 24224 (forward) or 9880 (HTTP)
2. Adds metadata: hostname, timestamp, source_type
3. Parses JSON messages if present
4. Buffers to disk (crash-safe)
5. Bulk inserts to OpenSearch indices `logs-YYYY.MM.DD`

**OpenSearch Storage**:
- Index pattern: `logs-*` (daily indices)
- Retention: Configurable via ILM policies
- Searchable via OpenSearch Dashboards or REST API

**Why this path?**
- Fluentd is purpose-built for log collection and transport
- Reliable buffering, retry logic, and backpressure handling
- OpenSearch provides powerful full-text search and log analytics
- Decouples log ingestion from backend API load

---

### 2️⃣ **Metrics Pipeline** (Backend API → PostgreSQL)

**Path**: Service → Backend API → PostgreSQL

**Endpoint**: `POST http://backend:8080/api/metrics`

**Payload Example**:
```json
{
  "serviceName": "user-api",
  "cpuUsage": 45.2,
  "memoryUsage": 62.8,
  "diskIoBytes": 1048576,
  "networkIoBytes": 2097152,
  "responseTimeMs": 150,
  "requestCount": 1200,
  "errorRate": 0.02,
  "timestamp": "2026-03-08T10:30:00Z"
}
```

**Backend Processing** ([MetricsController.java](../../backend-service/src/main/java/com/api/monitoring/backend/controller/MetricsController.java)):
- Receives JSON via REST API
- Validates and normalizes data
- Inserts into `systemmetrics` table
- Returns confirmation response

**PostgreSQL Storage** (Table: `systemmetrics`):
```sql
CREATE TABLE systemmetrics (
    id BIGSERIAL PRIMARY KEY,
    api_log_id BIGINT,
    service_name VARCHAR(255) NOT NULL,
    cpu_usage_percent DOUBLE PRECISION,
    memory_usage_percent DOUBLE PRECISION,
    disk_io_bytes BIGINT,
    network_io_bytes BIGINT,
    response_time_ms BIGINT,
    request_count INTEGER,
    error_rate DOUBLE PRECISION,
    metric_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Why this path?**
- Backend already implements `/api/metrics` endpoint
- PostgreSQL provides relational data model for time-series analysis
- ML service reads directly from Postgres for anomaly detection
- No need to introduce new infrastructure components

---

### 3️⃣ **Traces Pipeline** (Backend API → PostgreSQL)

**Path**: Service → Backend API → PostgreSQL

**Endpoint**: `POST http://backend:8080/api/traces/ingest`

**Payload Example**:
```json
{
  "traceId": "abc123xyz789",
  "spanId": "span001",
  "parentSpanId": null,
  "serviceName": "order-service",
  "operationName": "POST /orders",
  "startTime": "2026-03-08T10:30:00.123Z",
  "endTime": "2026-03-08T10:30:00.456Z",
  "duration": 333,
  "statusCode": 200,
  "tags": {
    "http.method": "POST",
    "http.url": "/orders",
    "user.id": "12345"
  },
  "logs": []
}
```

**Backend Processing** ([TracesController.java](../../backend-service/src/main/java/com/api/monitoring/backend/controller/TracesController.java)):
- Receives trace spans via REST API
- Stores in `distributedtraces` table
- Supports batch ingestion via `/api/traces/ingest/batch`

**PostgreSQL Storage** (Table: `distributedtraces`):
```sql
CREATE TABLE distributedtraces (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(255) NOT NULL,
    span_id VARCHAR(255) NOT NULL,
    parent_span_id VARCHAR(255),
    service_name VARCHAR(255),
    operation_name VARCHAR(500),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration BIGINT,
    status_code INTEGER,
    tags JSONB,
    logs JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Why this path?**
- Backend already implements `/api/traces/ingest` endpoint
- PostgreSQL JSONB storage for flexible span attributes
- Enables correlation with metrics in SQL queries
- ML service can join traces with metrics for multi-modal analysis

---

## 🔧 Component Responsibilities

| Component | Role | Signals Handled | Storage Backend |
|-----------|------|-----------------|-----------------|
| **Fluentd** | Log collector and shipper | Logs only | → OpenSearch |
| **Backend API** | Metrics/traces ingestion + business logic | Metrics, Traces | → PostgreSQL |
| **OpenSearch** | Log storage and search | Logs | Native storage |
| **PostgreSQL** | Relational data store | Metrics, Traces, Anomalies | Native storage |
| **ML Service** | Anomaly detection | Reads: Logs, Metrics, Traces | Consumes from Postgres |

---

## 🏗️ Infrastructure Components

### Docker Compose Services

**Currently Running** ✅:
```yaml
services:
  # Log Storage
  opensearch:
    image: opensearchproject/opensearch:2.17.0
    ports: ["9200:9200"]  # ✅ RUNNING
    
  # Log Collector
  fluentd:
    build: ./fluentd
    ports:
      - "24224:24224"     # Forward protocol
      - "9880:9880"       # HTTP input
      - "24231:24231"     # Prometheus metrics
      - "8888:8888"       # Health check
    volumes:
      - ./fluent.conf:/fluentd/etc/fluent.conf
      - fluentd_buffer:/fluentd/log  # ✅ RUNNING
      
  # Metrics & Traces Storage
  postgres:
    image: postgres:16
    ports: ["5433:5432"]  # ✅ RUNNING
    
  # Frontend Dashboard
  frontend:
    build: ../../frontend
    ports: ["3000:80"]  # ✅ RUNNING
    
  # Mock API for testing
  fake-server:
    build: ../../frontend/fake-server
    ports: ["8082:8082"]  # ✅ RUNNING
```

**Currently Commented Out** 💤:
```yaml
  # Backend API (Metrics/Traces ingestion)
  # Uncomment to enable - run: docker compose up -d --build backend
  # backend:
  #   build: ../../backend-service
  #   ports: ["8081:8080"]
  #   environment:
  #     SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/api_monitoring
```

**Separate Process** (Not in Docker):
```bash
# ML Service - run locally with Python
cd ml-service
python api/server.py  # Runs on http://localhost:9000
```

---

## 🚦 Service Communication Patterns

### Log Emission (Service → Fluentd)

**Option 1: Fluentd Forward Protocol** (Recommended)
```java
// With fluent-logger-java
FluentLogger logger = FluentLogger.getLogger("app.backend", "fluentd", 24224);
Map<String, Object> data = new HashMap<>();
data.put("message", "User login successful");
data.put("userId", 12345);
data.put("level", "INFO");
logger.log("login", data);
```

**Option 2: HTTP POST**
```bash
curl -X POST http://fluentd:9880/app.logs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "User login successful",
    "userId": 12345,
    "level": "INFO",
    "timestamp": "2026-03-08T10:30:00Z"
  }'
```

### Metrics Emission (Service → Backend API)

```bash
curl -X POST http://backend:8080/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "serviceName": "user-api",
    "cpuUsage": 45.2,
    "memoryUsage": 62.8,
    "responseTimeMs": 150,
    "requestCount": 1200,
    "errorRate": 0.02
  }'
```

### Traces Emission (Service → Backend API)

```bash
curl -X POST http://backend:8080/api/traces/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "traceId": "abc123",
    "spanId": "span001",
    "serviceName": "order-service",
    "operationName": "POST /orders",
    "startTime": "2026-03-08T10:30:00.123Z",
    "endTime": "2026-03-08T10:30:00.456Z",
    "duration": 333
  }'
```

---

## 📈 Benefits of Option B

### ✅ **Minimal Migration Risk**
- No changes to existing backend API contracts
- ML pipeline continues reading from Postgres unchanged
- Frontend dashboards work with existing endpoints

### ✅ **Right Tool for Right Job**
- Fluentd handles high-volume log shipping with proven reliability
- Backend API provides schema validation and business logic
- PostgreSQL enables relational queries across signals

### ✅ **Cost-Effective**
- Reuses existing infrastructure (Postgres, Spring Boot)
- No need for separate metrics/traces storage like Jaeger, Prometheus, etc.
- Lower operational complexity than multi-backend setups

### ✅ **ML/Analytics Friendly**
- All structured data (metrics, traces, anomalies) in one database
- Easy SQL joins for multi-modal analysis
- Direct access for ML service without cross-system queries

### ✅ **Future-Proof**
- Clear migration path: Services can switch to OpenTelemetry SDKs later
- OTel Collector can be added as a facade in front of backend APIs
- Fluentd can remain as log collector even with OTel migration

---

## 🚫 What Option B Does NOT Do

### ❌ **No OpenTelemetry (Yet)**
- This is by design to minimize rework
- Can be added later when needed
- See "Migration Path" section below

### ❌ **No Unified Collector**
- Logs and metrics/traces use different paths
- This is intentional - each path is optimized for its signal type

### ❌ **No Prometheus/Jaeger**
- Metrics stay in Postgres (not Prometheus TSDB)
- Traces stay in Postgres (not Jaeger or Zipkin)
- Trade-off: Simpler stack vs. specialized backends

---

## 🛤️ Future Migration Path (Option B → Full OTel)

When ready to adopt OpenTelemetry fully:

### Phase 1: Add OTel Collector (Sidecar Mode)
```
Service (OTel SDK) → OTel Collector → Backend API (/api/metrics, /api/traces)
                                    ↘ OpenSearch (logs via OTLP)
```
- Services emit OTLP (OpenTelemetry Protocol)
- OTel Collector transforms OTLP → backend API JSON format
- No backend changes needed

### Phase 2: Migrate Backends (Optional)
```
Service (OTel SDK) → OTel Collector → Prometheus (metrics)
                                    → Jaeger (traces)
                                    → OpenSearch (logs)
```
- Replace backend API with specialized backends
- Migrate ML service to read from new backends
- Full cloud-native observability stack

---

## 🔍 Observability Access Points

### Logs
- **OpenSearch** (HTTP): http://localhost:9200
- **OpenSearch Dashboards**: http://localhost:5601 (if enabled)
- **REST Query**: `curl http://localhost:9200/logs-*/_search?pretty`
- **Fluentd Health**: http://localhost:8888/api/plugins.json

### Metrics  
- **Backend API** (if running): `http://localhost:8081/api/metrics` (POST)
- **PostgreSQL Direct**: Query `systemmetrics` table
- **Connection**: `psql -h localhost -p 5433 -U api_monitor -d api_monitoring`

### Traces
- **Backend API** (if running): `http://localhost:8081/api/traces/ingest` (POST)
- **PostgreSQL Direct**: Query `distributedtraces` table
- **Frontend Dashboard**: http://localhost:3000 (shows fake data via fake-server)

### ML Predictions
- **ML Service Predictions**: `http://localhost:9000/v1/predict` (POST)
- **ML Service Health**: `http://localhost:9000/health` (GET)
- **Note**: ML service must be started separately with Python

### System Health
- **Fluentd**: http://localhost:8888/api/plugins.json
- **Fluentd Metrics**: http://localhost:24231/metrics
- **OpenSearch Cluster**: http://localhost:9200/_cluster/health
- **PostgreSQL**: `psql -h localhost -p 5433 -U api_monitor -d api_monitoring`

---

## 📚 Related Documentation

- [Fluentd Configuration](../docker/fluent.conf) - Log collector config
- [API Contracts](api-contracts.md) - Backend API endpoints
- [Docker Compose](../docker/docker-compose.yml) - Infrastructure setup
- [Infrastructure README](../README.md) - Deployment guide

---

## 🎓 Key Takeaways

1. **Logs**: Fluentd → OpenSearch (high-volume, search-optimized)
2. **Metrics**: Backend API → PostgreSQL (relational, ML-friendly)
3. **Traces**: Backend API → PostgreSQL (relational, ML-friendly)
4. **ML Pipeline**: Reads from PostgreSQL (unchanged)
5. **Migration Path**: Can add OTel later without disruption

This architecture balances **pragmatism** (minimal changes) with **best practices** (right tool for each signal type).
