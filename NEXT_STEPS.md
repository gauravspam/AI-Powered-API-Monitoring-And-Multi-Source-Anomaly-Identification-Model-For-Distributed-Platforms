# Project Implementation Roadmap

## Project Overview

**Project Name:** AI-Powered API Monitoring and Multi-Source Anomaly Identification Model for Distributed Platforms

**Current State:** Core ML models trained and functional
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
│  Models: MSIF-LSTM + PLE-GRU → Hybrid Ensemble                              │
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

## Completed ML Training

### Model Performance (AIOps 2020 Dataset)

| Model | Best F1 Score | Training Hardware |
|-------|----------------|-------------------|
| MSIF-LSTM | **90%** | GTX 1660 Super (6GB) |
| PLE-GRU | **92.6%** | GTX 1660 Super (6GB) |

### Training Details

- **Dataset**: AIOps 2020 Challenge (train-ticket microservice system)
- **Training Samples**: ~2500 sequences
- **Anomaly Rate**: ~5.8% (144 anomalies out of 2500)
- **Key Fix**: UTC+8 timezone alignment for timestamp matching
- **Training Epochs**: 60 epochs with early stopping
- **Hyperparameters**: 
  - Hidden dim: 256
  - Learning rate: 0.0005
  - Batch size: 16

### Model Files

```
ml-service/models/enhanced/
├── metric_encoder_aiops.pth    # TCN metric encoder (616KB)
├── msif_lstm_strict.pth       # MSIF-LSTM model (12.3MB)
└── ple_gru_strict.pth          # PLE-GRU model (28.8MB)
```

### Training Commands

```bash
cd ml-service

# Install PyTorch with CUDA (for GPU training)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Train MSIF-LSTM
python train_aiops_fixed.py --model msif --epochs 60 --batch 16 --hidden 256 --lr 0.0005

# Train PLE-GRU
python train_aiops_fixed.py --model ple --epochs 60 --batch 16 --hidden 256 --lr 0.0005
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

#### 5.3 Scheduler
- [ ] Add APScheduler or similar:
  - [ ] Run prediction every 2 minutes
  - [ ] Handle missed runs
  - [ ] Add jitter to prevent thundering herd

---

### Phase 6: Alert System (Priority: HIGH)
*Goal: Send notifications via Teams, Slack, Email, PagerDuty*

#### 6.1 Alert Service
- [ ] Create AlertService:
  - [ ] Queue alerts for processing
  - [ ] Rate limiting (prevent alert storms)
  - [ ] Retry logic for failed sends
  - [ ] Deduplication (same alert within X minutes)

#### 6.2 Microsoft Teams Integration
- [ ] Create Teams notification channel:
  - [ ] Incoming webhook configuration
  - [ ] Adaptive cards format

#### 6.3 Slack Integration
- [ ] Create Slack notification channel:
  - [ ] Incoming webhook configuration
  - [ ] Block kit message format
  - [ ] Channel routing by severity

#### 6.4 Email Integration
- [ ] Configure SMTP settings (from Vault):
  - [ ] Gmail/SendGrid/SMTP relay
  - [ ] HTML email templates

#### 6.5 PagerDuty Integration
- [ ] Create PagerDuty channel:
  - [ ] Events API v2 integration
  - [ ] Severity mapping to PagerDuty urgency

---

### Phase 7: Frontend Smart Polling (Priority: HIGH)
*Goal: Efficient frontend updates with minimal polling*

#### 7.1 Backend API Enhancement
- [ ] Add prediction metadata endpoint

#### 7.2 Smart Polling Implementation
- [ ] Implement in frontend:
```javascript
const pollForUpdates = async () => {
  const latest = await api.get('/api/predictions/latest');
  if (latest.prediction_time !== lastPredictionTime) {
    setNewAlertCount(latest.alert_count);
    showBadge(true);
  }
};
```

#### 7.3 User Interface Updates
- [ ] Add alert badge
- [ ] Click badge → refresh dashboard
- [ ] Keep manual refresh button

---

## Quick Wins (Can Be Done Anytime)

### Documentation
- [ ] Create architecture diagrams
- [ ] Create API Postman collection
- [ ] Create runbook for operations

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

---

## How to Use This File

1. **Start with Phase 1** - Secret injection is foundational
2. **Phase 2-4** - Collection layer (gRPC, Fluent Bit, OTel)
3. **Phase 5-7** - ML processing (batching, encoders, models)
4. **Update this file** as items are completed

---

*Last Updated: 2026-04-14*

*Architecture Version: 1.1*

*ML Models Trained and Ready*
