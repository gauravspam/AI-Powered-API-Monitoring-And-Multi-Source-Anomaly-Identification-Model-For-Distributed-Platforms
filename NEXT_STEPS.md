# Project Implementation Roadmap

## Project Overview

**Project Name:** AI-Powered API Monitoring and Multi-Source Anomaly Identification Model for Distributed Platforms

**Current State:** Core components implemented and functional
**Target State:** Production-ready enterprise monitoring platform

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SOURCES                                           │
│                                                                              │
│  Type 1: Your Services (gRPC)                                              │
│  Type 2: Legacy Apps (Fluent Bit)                                          │
│  Type 3: Cloud/SaaS (OTel Collector)                                       │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECRET INJECTION (HashiCorp Vault)                        │
│                                                                              │
│  - Dynamic database credentials                                             │
│  - TLS certificates for mTLS                                                │
│  - API keys for services                                                    │
│  - FREE Open Source Edition                                                 │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       COLLECTOR AGENT LAYER                                  │
│                                                                              │
│  - gRPC Receiver (Primary for your microservices)                          │
│  - Fluent Bit (Legacy app support)                                         │
│  - OTel Collector (Cloud/SaaS support)                                     │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUENTD (Central Aggregator)                       │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OPENSEARCH                                         │
│                                                                              │
│  Stores: logs, traces, metrics, anomalies                                   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               │ Batch query every 2 minutes
                               │ 5000 logs + 5000 traces + 5000 metrics
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ML SERVICE                                         │
│                                                                              │
│  Encoders: Metric → Log → Trace → Embeddings                                │
│  Models: MSIF-LSTM + PLE-GRU → Hybrid Ensemble                             │
│                                                                              │
│  Severity: CRITICAL(≥0.8) | HIGH(≥0.6) | MEDIUM(≥0.4) | LOW(<0.4)         │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ALERT SYSTEM                                         │
│                                                                              │
│  Channels: Microsoft Teams | Slack | Email | PagerDuty                     │
│  Triggered on: CRITICAL and HIGH severity                                  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                                   │
│                                                                              │
│  Smart Polling: Check prediction_time, show badge, manual refresh            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Secret Injection with HashiCorp Vault (Priority: HIGH)
*Goal: Secure credential management - FREE and self-hosted*

#### 1.1 Vault Setup
- [ ] Install HashiCorp Vault (Open Source - FREE)
- [ ] Run Vault in dev mode or production mode
- [ ] Configure secrets engines:
  - [ ] KV secrets engine (version 2) for general secrets
  - [ ] Database secrets engine for PostgreSQL credentials
  - [ ] PKI secrets engine for TLS certificates

#### 1.2 Vault Integration
- [ ] Implement Direct API integration (simpler for B.Tech project):
  - [ ] Add `vault` Python client to ML service
  - [ ] Add `vault` dependency to backend
  - [ ] Create VaultServiceClient utility
- [ ] Configure secrets:
  - [ ] PostgreSQL username/password
  - [ ] OpenSearch credentials
  - [ ] Alert service API keys (Teams, Slack, Email, PagerDuty)

#### 1.3 Dynamic Credentials
- [ ] Implement dynamic database credentials from Vault
- [ ] Implement certificate rotation via Vault PKI
- [ ] Add lease renewal handling

**Vault Configuration Example:**
```bash
# Start Vault dev server (for testing)
vault server -dev

# Or production-ready with Docker:
docker run -d --name=vault \
  -p 8200:8200 \
  -e VAULT_ADDR=http://localhost:8200 \
  vault server -config=/vault/config.hcl
```

---

### Phase 2: gRPC Receiver Service (Priority: HIGH)
*Goal: Replace REST API ingestion with secure gRPC*

#### 2.1 Proto Definition
- [ ] Create `proto/observability.proto`:
  - [ ] LogEntry message
  - [ ] MetricEntry message
  - [ ] TraceEntry message
  - [ ] IngestLog/Metric/Trace RPC methods
  - [ ] BatchIngest methods for bulk operations

#### 2.2 gRPC Server Implementation
- [ ] Create new service: `grpc-receiver/`
- [ ] Implement:
  - [ ] LogIngestService (receives logs via gRPC)
  - [ ] MetricIngestService (receives metrics via gRPC)
  - [ ] TraceIngestService (receives traces via gRPC)
- [ ] Add mTLS configuration:
  - [ ] Server certificate validation
  - [ ] Client certificate validation
  - [ ] Encrypted communication

#### 2.3 Source Service Updates
- [ ] Add gRPC clients to existing services:
  - [ ] Generate proto clients
  - [ ] Update logging to use gRPC instead of REST
  - [ ] Get TLS certificates from Vault

---

### Phase 3: Fluent Bit for Legacy Support (Priority: MEDIUM)
*Goal: Support legacy applications that write to files*

#### 3.1 Fluent Bit Configuration
- [ ] Add Fluent Bit to docker-compose:
  - [ ] Configure input: tail plugin for log files
  - [ ] Configure output: forward to Fluentd
  - [ ] Configure filters for parsing
- [ ] Create Fluent Bit config for legacy apps:
  - [ ] Parse Log4j2 JSON format
  - [ ] Parse plain text logs
  - [ ] Add metadata (hostname, service name)

#### 3.2 Legacy App Integration
- [ ] Document how legacy apps should write logs
- [ ] Create Log4j2 appender configuration example
- [ ] Test end-to-end flow

---

### Phase 4: OTel Collector for Cloud/SaaS (Priority: MEDIUM)
*Goal: Support cloud services and SaaS integrations*

#### 4.1 OTel Collector Setup
- [ ] Add OTel Collector to docker-compose:
  - [ ] Configure receivers:
    - [ ] OTLP receiver (for gRPC)
    - [ ] HTTP receiver (for SaaS webhooks)
  - [ ] Configure processors:
    - [ ] Batch processor
    - [ ] Memory limiter
    - [ ] Resource attributes
  - [ ] Configure exporters:
    - [ ] Forward to Fluentd
    - [ ] Debug exporter (for testing)

#### 4.2 Cloud Service Integration
- [ ] Document OTel SDK integration for:
  - [ ] AWS Lambda
  - [ ] GCP Cloud Run
  - [ ] Azure Functions
- [ ] Create sample configurations

---

### Phase 5: ML Service Batch Processing (Priority: HIGH)
*Goal: Process data in batches every 2 minutes*

#### 5.1 Batch Configuration
- [ ] Make batch sizes configurable:
```python
# config.py
BATCH_SIZE_LOGS = 5000       # Configurable per modality
BATCH_SIZE_TRACES = 5000
BATCH_SIZE_METRICS = 5000
BATCH_INTERVAL_SECONDS = 120  # 2 minutes
```

#### 5.2 Batch Query Service
- [ ] Create BatchQueryService:
  - [ ] Query OpenSearch for recent data
  - [ ] Maintain batch state
  - [ ] Handle partial batches
  - [ ] Track processed record IDs (avoid duplicates)
- [ ] Implement batch size optimization:
  - [ ] Adaptive batching based on hardware
  - [ ] Memory-efficient processing

#### 5.3 Scheduler
- [ ] Add APScheduler or similar:
  - [ ] Run prediction every 2 minutes
  - [ ] Handle missed runs
  - [ ] Add jitter to prevent thundering herd

#### 5.4 Hardware Considerations
- [ ] Document batch size recommendations:
```
CPU Only (no GPU):
- Batch size: 2,500 - 5,000 per modality
- Memory: 8GB+ recommended

Small GPU (4GB VRAM):
- Batch size: 5,000 - 10,000 per modality
- Memory: 8GB system + 4GB GPU

Large GPU (16GB+ VRAM):
- Batch size: 10,000 - 50,000 per modality
- Memory: 16GB system + 16GB GPU
```

---

### Phase 6: Encoders Implementation (Priority: HIGH)
*Goal: Transform raw data to embeddings for ML models*

#### 6.1 Metric Encoder
- [ ] Normalize metrics:
  - [ ] CPU/Memory: 0-100 → 0-1 (min-max)
  - [ ] Response time: log scale + normalize
  - [ ] Error rate: already 0-1
  - [ ] Request count: log scale + normalize
- [ ] Create fixed-size embedding vector
- [ ] Handle missing values

#### 6.2 Log Encoder
- [ ] Text preprocessing:
  - [ ] Tokenization
  - [ ] Lowercase
  - [ ] Remove special characters
  - [ ] Handle error keywords
- [ ] Embedding approaches:
  - [ ] TF-IDF vectorization
  - [ ] Pre-trained word embeddings (Word2Vec/FastText)
  - [ ] Custom learned embeddings
- [ ] Create fixed-size embedding vector

#### 6.3 Trace Encoder
- [ ] Extract features:
  - [ ] Duration (log normalized)
  - [ ] Span count
  - [ ] Error count
  - [ ] Service graph features
- [ ] Create fixed-size embedding vector
- [ ] Handle trace structure (parent-child relationships)

#### 6.4 Fusion Layer
- [ ] Concatenate embeddings:
```python
combined_embedding = concat(
    metric_embedding,    # [dim_m]
    log_embedding,       # [dim_l]
    trace_embedding      # [dim_t]
)  # Total: [dim_m + dim_l + dim_t]
```

---

### Phase 7: Hybrid Model Enhancement (Priority: HIGH)
*Goal: Improve MSIF-LSTM + PLE-GRU hybrid ensemble*

#### 7.1 Model Configuration
- [ ] Update models to accept batch embeddings
- [ ] Configure ensemble weights:
```python
# Configurable weights
MSIF_WEIGHT = 0.6
PLE_WEIGHT = 0.4
FUSION_THRESHOLD = 0.7
```

#### 7.2 Severity Classification
- [ ] Implement severity levels:
```python
def score_to_severity(score):
    if score >= 0.8: return "CRITICAL"  # Immediate alert
    elif score >= 0.6: return "HIGH"    # Alert in 1 min
    elif score >= 0.4: return "MEDIUM"  # Log only
    else: return "LOW"                   # Ignore
```

#### 7.3 Model Output
- [ ] Write predictions back to OpenSearch:
```json
{
  "prediction_id": "uuid",
  "batch_id": "uuid",
  "timestamp": "2026-04-11T10:30:00Z",
  "final_score": 0.85,
  "severity": "HIGH",
  "msif_score": 0.82,
  "ple_score": 0.78,
  "fusion_method": "weighted_ensemble",
  "confidence": 0.85,
  "affected_services": ["api-gateway", "user-service"],
  "affected_metrics": ["response_time", "error_rate"]
}
```

---

### Phase 8: Alert System (Priority: HIGH)
*Goal: Send notifications via Teams, Slack, Email, PagerDuty*

#### 8.1 Alert Service
- [ ] Create AlertService:
  - [ ] Queue alerts for processing
  - [ ] Rate limiting (prevent alert storms)
  - [ ] Retry logic for failed sends
  - [ ] Deduplication (same alert within X minutes)

#### 8.2 Microsoft Teams Integration
- [ ] Create Teams notification channel:
  - [ ] Incoming webhook configuration
  - [ ] Adaptive cards format:
```json
{
  "type": "message",
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {
      "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "body": [
        {"type": "TextBlock", "text": "ANOMALY DETECTED", "weight": "bolder"},
        {"type": "TextBlock", "text": "Severity: HIGH"},
        {"type": "TextBlock", "text": "Score: 0.85"},
        {"type": "TextBlock", "text": "Affected: api-gateway"}
      ]
    }
  }]
}
```

#### 8.3 Slack Integration
- [ ] Create Slack notification channel:
  - [ ] Incoming webhook configuration
  - [ ] Block kit message format
  - [ ] Channel routing by severity

#### 8.4 Email Integration
- [ ] Configure SMTP settings (from Vault):
  - [ ] Gmail/SendGrid/SMTP relay
  - [ ] HTML email templates
  - [ ] Email grouping (digest vs immediate)

#### 8.5 PagerDuty Integration
- [ ] Create PagerDuty channel:
  - [ ] Events API v2 integration
  - [ ] Severity mapping to PagerDuty urgency
  - [ ] Auto-create incidents

---

### Phase 9: Frontend Smart Polling (Priority: HIGH)
*Goal: Efficient frontend updates with minimal polling*

#### 9.1 Backend API Enhancement
- [ ] Add prediction metadata endpoint:
```json
GET /api/predictions/latest
{
  "prediction_id": "uuid",
  "prediction_time": "2026-04-11T10:30:00Z",
  "severity": "HIGH",
  "alert_count": 5
}
```

#### 9.2 Smart Polling Implementation
- [ ] Implement in frontend:
```javascript
// Smart polling logic
const pollForUpdates = async () => {
  const latest = await api.get('/api/predictions/latest');
  
  if (latest.prediction_time !== lastPredictionTime) {
    // New prediction available
    setNewAlertCount(latest.alert_count);
    showBadge(true);
    lastPredictionTime = latest.prediction_time;
  }
};

// Poll every 30 seconds
setInterval(pollForUpdates, 30000);
```

#### 9.3 User Interface Updates
- [ ] Add alert badge (shows "N new alerts")
- [ ] Click badge → refresh dashboard with new data
- [ ] Keep manual refresh button
- [ ] Add settings for polling interval

#### 9.4 Optional: WebSocket (Future Enhancement)
- [ ] Add WebSocket endpoint for real-time updates
- [ ] Frontend connects on load
- [ ] Push new alerts immediately
- [ ] Fallback to polling if WebSocket fails

---

## Quick Wins (Can Be Done Anytime)

### Documentation
- [ ] Create architecture diagrams (using this file)
- [ ] Create API Postman collection
- [ ] Create runbook for operations
- [ ] Create troubleshooting guide

### Developer Experience
- [ ] Create dev container (devcontainer.json)
- [ ] Create one-command startup script
- [ ] Add pre-commit hooks
- [ ] Create CI/CD pipeline template

---

## Configuration Reference

### ML Service Batch Settings
```python
# ml-service/config.py
BATCH_SIZE_LOGS = 5000
BATCH_SIZE_TRACES = 5000
BATCH_SIZE_METRICS = 5000
BATCH_INTERVAL_SECONDS = 120  # 2 minutes
```

### Hardware Recommendations
| Hardware | Batch Size | Use Case |
|----------|------------|----------|
| CPU only | 2,500-5,000 | Development, testing |
| CPU + 4GB GPU | 5,000-10,000 | Small production |
| CPU + 16GB GPU | 10,000-50,000 | Medium production |
| CPU + 32GB+ GPU | 50,000+ | Large scale |

### Severity Thresholds
| Score Range | Severity | Action |
|-------------|----------|--------|
| 0.8 - 1.0 | CRITICAL | Immediate alert |
| 0.6 - 0.79 | HIGH | Alert in 1 minute |
| 0.4 - 0.59 | MEDIUM | Log only |
| 0.0 - 0.39 | LOW | Ignore |

---

## Dependencies Reference

### Free Tools (All Open Source)
| Tool | Purpose | License |
|------|---------|---------|
| HashiCorp Vault | Secret management | Open Source (FREE) |
| Fluent Bit | Log collection | Apache 2.0 |
| OTel Collector | Cloud observability | Apache 2.0 |
| Fluentd | Log aggregation | Apache 2.0 |
| OpenSearch | Search & analytics | Apache 2.0 |

### Cloud Services (Free Tiers)
| Service | Purpose | Free Tier |
|---------|---------|------------|
| Microsoft Teams | Alerts | Webhook free |
| Slack | Alerts | Webhook free |
| Gmail | Email | 500 emails/day |
| SendGrid | Email | 100 emails/day |
| PagerDuty | Incident management | Developer free |

---

## File Structure

```
project/
├── backend-service/              # Spring Boot backend
├── frontend/                     # React frontend
├── ml-service/                   # ML service
│   ├── src/
│   │   ├── encoders/           # NEW: Metric, Log, Trace encoders
│   │   ├── models/             # MSIF-LSTM, PLE-GRU, Hybrid
│   │   └── batch_processor.py   # NEW: Batch query and processing
│   ├── config.py               # NEW: Batch and model config
│   └── requirements.txt
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml  # UPDATED: Add Vault, Fluent Bit, OTel
│   │   ├── fluent-bit/          # NEW: Fluent Bit config
│   │   └── oTel-collector/      # NEW: OTel Collector config
│   └── vault/                   # NEW: Vault configuration
├── grpc-receiver/               # NEW: gRPC receiver service
├── proto/                       # NEW: Protocol buffer definitions
└── docs/
    └── architecture.md          # Architecture documentation
```

---

## How to Use This File

1. **Start with Phase 1** - Secret injection is foundational
2. **Phase 2-4** - Collection layer (gRPC, Fluent Bit, OTel)
3. **Phase 5-7** - ML processing (batching, encoders, models)
4. **Phase 8-9** - Alerting and frontend
5. **Update this file** as items are completed

---

## Tracking Progress

Use this format to track completion:
```
- [ ] Not started
- [x] Completed (date)
- [ ] In progress
- [ ] Blocked (reason)
```

Example:
```
- [x] Add Vault to docker-compose - 2026-04-11
- [ ] Implement gRPC proto definitions - In progress
- [ ] Add Fluent Bit configuration - Blocked: waiting for legacy app access
```

---

*Last Updated: 2026-04-11*

*Architecture Version: 1.0*

*Ready for implementation*