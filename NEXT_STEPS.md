# Project Implementation Roadmap

## Project Overview

**Project Name:** AI-Powered API Monitoring and Multi-Source Anomaly Identification Model for Distributed Platforms

**Current State:** 
- ML models trained and functional
- Backend REST APIs working
- Frontend dashboard operational
- Simulator page connected to ML service

**Target State:** Production-ready enterprise monitoring platform with:
- gRPC data ingestion
- Fluentd log aggregation
- Batch ML processing every 2 minutes
- Multi-channel alert system (Teams, Slack, Email, PagerDuty)

---

## Architecture Summary (Updated 2026-04-18)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA SOURCES                                        │
│                                                                              │
│  Type 1: Your Services (REST API) ← Currently working                     │
│  Type 2: Simulator (Manual testing) ← Currently working                   │
│  Type 3: gRPC (To be implemented)                                          │
│  Type 4: Fluent Bit (Legacy app support)                                   │
│  Type 5: OTel Collector (Cloud/SaaS support)                               │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUENTD (Central Aggregator)                             │
│                                                                              │
│  ✓ Enabled in docker-compose.yml                                           │
│  ✓ Configured routing:                                                      │
│    - logs.*    → OpenSearch                                                │
│    - metrics.* → Backend API → PostgreSQL                                   │
│    - traces.*  → Backend API → PostgreSQL                                   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
┌────────────────────────────────┐  ┌──────────────────────────────────────────┐
│         OPENSEARCH             │  │           POSTGRESQL                     │
│                                │  │                                          │
│  Stores: logs                  │  │  Stores: metrics, traces, anomalies     │
│  Query source for ML batch     │  │  Query source for frontend               │
└───────────────────────────────┬─┘  └──────────────────────────────┬───────────┘
                               │                                    │
                               │ Batch query every 2 min            │
                               │ 5000 logs + 5000 traces + 5000 metrics
                               ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ML SERVICE                                         │
│                                                                              │
│  Current: On-demand prediction via /predict/flexible                      │
│  To Add: Batch scheduler every 2 minutes                                    │
│                                                                              │
│  Encoders: Metric → Log → Trace → Embeddings                                │
│  Models: MSIF-LSTM + PLE-GRU → Hybrid Ensemble                              │
│                                                                              │
│  Severity: CRITICAL(≥0.8) | HIGH(≥0.6) | MEDIUM(≥0.4) | LOW(<0.4)           │
└──────────────────────────────┬───────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ALERT SYSTEM                                         │
│                                                                              │
│  To Implement:                                                              │
│  - Microsoft Teams (webhook)                                               │
│  - Slack (webhook)                                                          │
│  - Email (SMTP)                                                              │
│  - PagerDuty (API)                                                          │
│                                                                              │
│  Triggered on: CRITICAL and HIGH severity                                   │
└──────────────────────────────┬───────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                                   │
│                                                                              │
│  Pages: Overview | Dashboard | Metrics | Logs | Traces | Alerts | Simulator │
│  Data Source: PostgreSQL (metrics/traces) + OpenSearch (logs)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases (Updated Order)

### Phase 1: Fluentd Layer Setup ✅ COMPLETED 2026-04-18
*Goal: Enable Fluentd for log aggregation and routing*

#### 1.1 Enable Fluentd in docker-compose.yml
- [x] Uncomment Fluentd service in `infrastructure/docker/configs/docker-compose.yml`
- [x] Configure build context for fluentd.Dockerfile
- [x] Add environment variables for OpenSearch connection

#### 1.2 Configure fluent.conf routing
- [x] Route `logs.**` → OpenSearch (index: logs-YYYY.mm.dd)
- [x] Route `metrics.**` → Backend API (`http://backend:8080/api/metrics`)
- [x] Route `traces.**` → Backend API (`http://backend:8080/api/traces/ingest`)
- [x] Add buffering for reliability
- [x] Add retry logic for failed submissions

#### 1.3 Start Fluentd
```bash
cd infrastructure/docker/configs
docker compose up -d fluentd
```

#### 1.4 Test Fluentd
```bash
# Test log ingestion to OpenSearch
curl -X POST http://localhost:9880/logs.app \
  -d '{"message":"test error","level":"ERROR","service":"user-service"}'

# Test metrics to backend
curl -X POST http://localhost:9880/metrics.app \
  -d '{"cpu_usage":45,"memory_usage":60,"response_time_ms":120}'

# Verify in OpenSearch
curl http://localhost:9200/logs-*/_search?size=1

# Verify in PostgreSQL
docker exec postgres psql -U api_monitor -d api_monitoring -c "SELECT * FROM system_metrics LIMIT 3;"
```

---

### Phase 2: gRPC Receiver Service (Priority: HIGH)
*Goal: Add gRPC ingestion as alternative to REST APIs*

#### 2.1 Create gRPC Server Module
- [ ] Create `backend-service/src/main/java/com/api/monitoring/backend/grpc/`
- [ ] Add gRPC dependencies to `pom.xml`:
  ```xml
  <dependency>
      <groupId>io.grpc</groupId>
      <artifactId>grpc-spring-boot-starter</artifactId>
      <version>0.4.3</version>
  </dependency>
  <dependency>
      <groupId>io.grpc</groupId>
      <artifactId>grpc-netty</artifactId>
      <version>1.59.0</version>
  </dependency>
  ```

#### 2.2 Implement ObservabilityService
- [ ] Create `ObservabilityServiceImpl.java` based on `proto/observability.proto`
- [ ] Implement methods:
  - `IngestMetric(MetricRequest) → MetricResponse`
  - `IngestLog(LogRequest) → LogResponse`
  - `IngestTrace(TraceRequest) → TraceResponse`
  - `StreamTelemetry(stream of TelemetryData) → StreamResponse`

#### 2.3 gRPC Server Configuration
- [ ] Create `GrpcServerProperties.java` for config
- [ ] Add port configuration (default: 9090)
- [ ] Add TLS/mTLS configuration (optional)

#### 2.4 Forward to Storage
- [ ] Integrate with existing services (MetricsService, LogsService, TracesService)
- [ ] Forward metrics → PostgreSQL
- [ ] Forward logs → OpenSearch (via existing service)
- [ ] Forward traces → PostgreSQL

#### 2.5 Test gRPC Client
- [ ] Create sample gRPC client to send data
- [ ] Document proto usage

**File locations:**
- Proto: `proto/observability.proto`
- New gRPC server: `backend-service/src/main/java/com/api/monitoring/backend/grpc/`
- gRPC port: 9090

---

### Phase 3: ML Batch Processing (Priority: HIGH)
*Goal: Query OpenSearch every 2 minutes for batch prediction*

#### 3.1 Create Batch Scheduler Module
- [ ] Create `ml-service/api/batch_scheduler.py`

#### 3.2 OpenSearch Query Service
- [ ] Query recent logs (last 2 minutes, max 5000)
- [ ] Query recent metrics (last 2 minutes, max 5000)
- [ ] Query recent traces (last 2 minutes, max 5000)
- [ ] Track processed record IDs to avoid duplicates
- [ ] Handle partial batches

#### 3.3 ML Batch Processing
- [ ] Process batch through encoders (MetricEncoder, LogEncoder, TraceEncoder)
- [ ] Run through MSIF-LSTM model
- [ ] Run through PLE-GRU model
- [ ] Calculate Hybrid Ensemble score
- [ ] Apply rule-based boosting

#### 3.4 Store Predictions
- [ ] Save to PostgreSQL `anomaly_detections` table:
  - `hybrid_score`, `msif_score`, `ple_score`
  - `severity`, `confidence`
  - `modalities_present`, `fusion_method`
  - `prediction_timestamp`
- [ ] Optional: Update OpenSearch with scores

#### 3.5 Alert Integration
- [ ] Trigger alerts for CRITICAL/HIGH severity
- [ ] Send to alert service (Phase 4)

**Configuration:**
```python
# ml-service/api/config.py
BATCH_INTERVAL_SECONDS = 120  # 2 minutes
BATCH_SIZE_METRICS = 5000
BATCH_SIZE_LOGS = 5000
BATCH_SIZE_TRACES = 5000
```

---

### Phase 4: Alert System (Priority: HIGH)
*Goal: Send notifications via Teams, Slack, Email, PagerDuty*

#### 4.1 Alert Service Architecture
- [ ] Create `backend-service/src/main/java/com/api/monitoring/backend/service/AlertService.java`
- [ ] Create `backend-service/src/main/java/com/api/monitoring/backend/service/AlertQueueService.java`

#### 4.2 Alert Data Model
- [ ] Create `AlertRecord` entity:
  ```java
  // Already exists: com.api.monitoring.backend.model.AlertRecord
  // Fields needed: severity, message, channels, timestamp, sent
  ```

#### 4.3 Alert Channels Implementation

##### Microsoft Teams
- [ ] Create `TeamsAlertHandler.java`
- [ ] Configure incoming webhook URL
- [ ] Create Adaptive Card template:
  ```json
  {
    "type": "AdaptiveCard",
    "body": [
      {"type": "TextBlock", "text": "${severity}: ${message}", "weight": "bolder"},
      {"type": "FactSet", "facts": [
        {"title": "Service", "value": "${service}"},
        {"title": "Score", "value": "${score}"},
        {"title": "Time", "value": "${timestamp}"}
      ]}
    ],
    "actions": [{"type": "Action.OpenUrl", "title": "View Dashboard", "url": "${dashboardUrl}"}]
  }
  ```

##### Slack
- [ ] Create `SlackAlertHandler.java`
- [ ] Configure incoming webhook URL
- [ ] Create Block Kit message:
  ```json
  {
    "blocks": [
      {"type": "header", "text": {"type": "plain_text", "text": ":warning: ${severity} Alert"}},
      {"type": "section", "text": {"type": "mrkdwn", "text": "${message}"}},
      {"type": "context", "elements": [
        {"type": "mrkdwn", "text": "Service: ${service}"},
        {"type": "mrkdwn", "text": "Score: ${score}"}
      ]}
    ]
  }
  ```

##### Email
- [ ] Create `EmailAlertHandler.java`
- [ ] Configure SMTP settings (from environment or Vault):
  ```yaml
  spring.mail.host: smtp.gmail.com
  spring.mail.port: 587
  spring.mail.username: ${SMTP_USERNAME}
  spring.mail.password: ${SMTP_PASSWORD}
  ```
- [ ] Create HTML email template
- [ ] Support multiple recipients

##### PagerDuty
- [ ] Create `PagerDutyAlertHandler.java`
- [ ] Configure API key
- [ ] Map severity to PagerDuty urgency:
  - CRITICAL → P1 (high)
  - HIGH → P2 (high)
  - MEDIUM/LOW → P3/P4 (low)
- [ ] Include triggering data payload

#### 4.4 Alert Queue and Throttling
- [ ] Implement in-memory queue (or Redis)
- [ ] Rate limiting: max 10 alerts per minute per service
- [ ] Deduplication: ignore same alert within 5 minutes
- [ ] Retry logic: 3 retries with exponential backoff

#### 4.5 Alert Triggering
- [ ] Trigger from ML batch scheduler when:
  - `severity == CRITICAL` (score >= 0.8)
  - `severity == HIGH` (score >= 0.6)
- [ ] Queue alert with selected channels

---

### Phase 5: Frontend Integration (Priority: HIGH)
*Goal: Connect frontend to updated data flow*

#### 5.1 Update API Layer
- [ ] Ensure frontend queries PostgreSQL for metrics/traces
- [ ] Ensure frontend queries OpenSearch for logs (optional)

#### 5.2 Smart Polling
- [ ] Implement polling for new anomaly detections
- [ ] Add alert badge on new data

#### 5.3 Simulator Updates (Optional)
- [ ] Option to send data via gRPC instead of direct ML call
- [ ] Option to send via Fluentd HTTP endpoint

---

## Known Bugs Fixed (2026-04-18)

### ML Service Payload Handling
- [x] Fixed: `encode_metric()` - handle array of metrics (was failing with 400)
- [x] Fixed: `encode_traces()` - handle status_code as number (was comparing string to 400)
- [x] Fixed: `predict_flexible()` - handle array metrics in rule-based scoring

### Frontend
- [x] Fixed: Simulator.jsx - duplicate useState, Icon prop
- [x] Fixed: Traces.jsx - changed ScatterChart to BarChart
- [x] Fixed: Dashboard.jsx - removed Error Budget Burn card

### Database
- [x] PostgreSQL is accessible and storing data correctly

---

## Dependencies Reference

### Docker Services (infrastructure/docker/configs/docker-compose.yml)
| Service | Port | Status |
|---------|------|--------|
| PostgreSQL | 5433 | ✅ Running |
| OpenSearch | 9200 | ✅ Running |
| Fluentd | 24224, 9880, 8888 | 🔄 To start |

### Backend Services
| Service | Port | Status |
|---------|------|--------|
| Backend API | 8080 | ✅ Running |
| ML Service | 9000 | ✅ Running |
| gRPC Server | 9090 | 🔄 To implement |

### Frontend
| Service | Port | Status |
|---------|------|--------|
| Frontend | 5173 | ✅ Running |

---

## How to Use This File

1. **Start Fluentd** (Phase 1): `cd infrastructure/docker/configs && docker compose up -d fluentd`
2. **Implement gRPC** (Phase 2): Add gRPC server to backend
3. **Add ML batch** (Phase 3): Create batch scheduler in ML service
4. **Implement alerts** (Phase 4): Add all 4 notification channels
5. **Test end-to-end**: Send data → verify storage → verify ML prediction → verify alerts

---

## Quick Start Commands

```bash
# Start all infrastructure
cd infrastructure/docker/configs
docker compose up -d

# Verify services
docker compose ps
curl http://localhost:9200  # OpenSearch
curl http://localhost:5433  # PostgreSQL

# Start backend (in another terminal)
cd backend-service
./gradlew bootRun

# Start ML service (in another terminal)
cd ml-service
python api/main.py

# Start frontend (in another terminal)
cd frontend
npm run dev
```

---

*Last Updated: 2026-04-18*

*Architecture Version: 2.0*

*Changes:*
- Phase 1 (Fluentd) completed
- Phase 2-5 detailed steps added
- Known bugs documented
- Implementation order clarified
