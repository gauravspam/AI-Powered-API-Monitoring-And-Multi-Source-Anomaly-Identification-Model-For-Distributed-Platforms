# ML Service Documentation

## Overview

The ML service provides anomaly detection for distributed systems using a hybrid ensemble of deep learning models. It analyzes multi-modal telemetry data (metrics, logs, traces) and returns severity predictions.

**Tech Stack:**
- Python 3.8+
- FastAPI
- PyTorch 2.0+
- scikit-learn

**Port:** `9000`

---

## Quick Start

```bash
cd ml-service
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 9000
```

---

## Project Structure

```
ml-service/
├── api/
│   └── main.py               # FastAPI app & endpoints
├── model_defs/
│   ├── msif_lstm.py         # MSIF-LSTM model
│   ├── ple_gru.py           # PLE-GRU model
│   ├── ensemble.py          # Hybrid ensemble
│   ├── metric_encoder.py    # Metric encoder
│   ├── log_encoder.py       # Log encoder
│   └── trace_encoder.py     # Trace encoder
├── training/
│   └── train_model.py       # Model training script
├── config/
│   └── settings.py          # Configuration
├── models/                   # Saved model weights
└── requirements.txt
```

---

## API Endpoints

### Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict/flexible` | Multi-modal anomaly prediction |

**Request Body:**
```json
{
  "severity": "MEDIUM",
  "metrics": [
    {
      "cpu_usage": 65,
      "memory_usage": 70,
      "response_time": 900,
      "error_rate": 15,
      "request_count": 500,
      "service_id": "service-1"
    }
  ],
  "logs": [
    {
      "level": "ERROR",
      "message": "Connection timeout",
      "service": "service-1",
      "timestamp": "2026-04-18T10:00:00Z"
    }
  ],
  "traces": [
    {
      "trace_id": "trace-123",
      "span_id": "span-1",
      "service": "service-1",
      "operation": "http.request",
      "duration_ms": 1500,
      "status_code": 500
    }
  ]
}
```

**Response:**
```json
{
  "hybrid_score": 0.52,
  "msif_score": 0.48,
  "ple_score": 0.55,
  "severity": "MEDIUM",
  "confidence": 0.85,
  "fusion_method": "weighted_ensemble"
}
```

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |

---

## Models

### MSIF-LSTM (Multi-Scale Input Feature LSTM)
- Encodes time-series metrics and logs
- Captures temporal patterns across multiple scales

### PLE-GRU (Progressive Learning Engine GRU)
- Hierarchical attention for traces
- Progressive feature extraction

### Hybrid Ensemble
- Combines MSIF-LSTM and PLE-GRU predictions
- Weighted fusion based on confidence scores

---

## Severity Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| NORMAL | 0.00 - 0.15 | No anomaly |
| LOW | 0.15 - 0.35 | Minor anomaly |
| MEDIUM | 0.35 - 0.65 | Moderate anomaly |
| HIGH | 0.65 - 0.85 | Severe anomaly |
| CRITICAL | 0.85 - 1.00 | Critical anomaly |

---

## Configuration

Environment variables:

```env
MODEL_PATH=models/
PORT=9000
LOG_LEVEL=INFO
```

---

## Training

To train the models:

```bash
cd ml-service
python training/train_model.py
```

Training data should include labeled examples with severity labels (NORMAL, LOW, MEDIUM, HIGH, CRITICAL).