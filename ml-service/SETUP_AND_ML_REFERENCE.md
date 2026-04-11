# ML Service - Setup & ML Reference Guide

## Overview

The ML Service is a Flask-based Python microservice that provides anomaly detection for the API Monitoring Platform. It uses multiple ML models to detect anomalies in API metrics, logs, and traces.

**Tech Stack:**
- Flask 2.3+ for REST API
- PyTorch for deep learning models
- TensorFlow for additional models
- NumPy, Pandas, Scikit-learn for data processing

**Access URL:** `http://localhost:9000`

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Starting the ML Service](#starting-the-ml-service)
3. [Project Structure](#project-structure)
4. [API Endpoints](#api-endpoints)
5. [ML Models](#ml-models)
6. [Request/Response Examples](#requestresponse-examples)
7. [Configuration](#configuration)
8. [Training](#training)
9. [Building & Running](#building--running)
10. [Integration with Backend](#integration-with-backend)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.8+ | Required for PyTorch/TensorFlow |
| pip | 20+ | Package manager |
| CUDA | 11.8+ | Optional for GPU acceleration |

### Install Dependencies

```powershell
cd ml-service
pip install -r requirements.txt
```

---

## Starting the ML Service

### Option 1: Run Directly

```powershell
cd ml-service/api
python app_multimodal.py
```

### Option 2: Run with Flask

```powershell
cd ml-service/api
flask run --host=0.0.0.0 --port=9000
```

### Option 3: Run with Gunicorn

```powershell
cd ml-service/api
gunicorn -w 2 -b 0.0.0.0:9000 app_multimodal:app
```

### Option 4: Run with Docker

```powershell
cd ml-service
docker build -t ml-service .
docker run -d -p 9000:9000 ml-service
```

The ML service will start on **http://localhost:9000**

---

## Project Structure

```
ml-service/
├── api/                    # Flask API
│   ├── app_multimodal.py   # Main Flask app
│   ├── routes.py         # API routes
│   └── __init__.py
├── src/                   # ML models
│   ├── models/
│   │   ├── hybrid_fusion.py      # Ensemble model
│   │   ├── msif_lstm_model.py  # MSIF-LSTM model
│   │   ├── ple_gru_model.py   # PLE-GRU model
│   │   ├── metric_encoder.py
│   │   ├── log_encoder.py
│   │   └── trace_encoder.py
│   └── __init__.py
├── models/                 # Trained model weights
│   ├── enhanced/
│   │   ├── msif_lstm.pth
│   │   └── ple_gru.pth
│   ├── microservices/
│   │   ├── microservices_lstm.h5
│   │   └── microservices_plegru.h5
│   └── encoders/
│       ├── metric/
│       ├── log/
│       └── trace/
├── config/
│   └── settings.py
├── training/               # Training scripts
│   ├── pretrain/
│   └── fusion/
├── utils/
├── requirements.txt
└── Dockerfile
```

---

## API Endpoints

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health status |

**Response:**
```json
{
  "status": "healthy",
  "device": "cpu",
  "models_loaded": ["msif", "ple", "fusion"]
}
```

---

### Predict (Main Endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict` | Main prediction endpoint |

**Request:**
```json
{
  "response_time": 2500,
  "status_code": 500,
  "cpu_usage": 85.0,
  "memory_usage": 70.0,
  "error_rate": 0.15,
  "request_count": 1500
}
```

**Response:**
```json
{
  "status": "success",
  "hybrid_score": 0.72,
  "msif_score": 0.68,
  "ple_score": 0.72,
  "severity": "HIGH",
  "fusion_method": "rule-based-fallback",
  "confidence": 0.6
}
```

---

### Multimodal Predict

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict/multimodal` | Multi-source prediction |

**Request:**
```json
{
  "metrics": 0.5,
  "logs": 0.3,
  "traces": 0.8
}
```

**Response:**
```json
{
  "status": "ANOMALY",
  "final_score": 0.85,
  "details": {
    "msif_score": 0.82,
    "ple_score": 0.78,
    "fusion_method": "weighted_ensemble",
    "model_agreement": 0.04
  }
}
```

---

### Test Predict

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict/test` | Test with controllable scores |

**Request:**
```json
{
  "msif_score": 0.9,
  "ple_score": 0.85
}
```

**Response:**
```json
{
  "status": "ANOMALY",
  "final_score": 0.88,
  "details": {
    "msif_score": 0.9,
    "ple_score": 0.85,
    "fusion_method": "weighted_ensemble",
    "model_agreement": 0.05
  }
}
```

---

### Model Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/model-info` | Get model information |

**Response:**
```json
{
  "service": "ml-anomaly-detection",
  "version": "1.0.0",
  "models": {
    "msif_lstm": {
      "name": "Multi-Scale Isolation Forest + LSTM",
      "window_size": 60,
      "features": ["response_time", "cpu", "memory", "error_rate", "request_count"]
    },
    "ple_gru": {
      "name": "Probabilistic Label Enhancement + GRU",
      "window_size": 1440,
      "features": 7
    }
  },
  "fusion": {
    "method": "Hybrid weighted combination",
    "msif_weight": 0.6,
    "ple_weight": 0.4,
    "threshold": 0.7
  }
}
```

---

## ML Models

### 1. MSIF-LSTM (Multi-Scale Isolation Forest + LSTM)

**Purpose:** 60-minute window anomaly detection

**Architecture:**
- Embedding dimension: 3
- LSTM hidden dimension: 64
- Hybrid of Isolation Forest + LSTM

**Features:**
- response_time
- cpu_usage
- memory_usage
- error_rate
- request_count

**Window:** 60 timesteps

**File:** `models/enhanced/msif_lstm.pth`

---

### 2. PLE-GRU (Probabilistic Label Enhancement + GRU)

**Purpose:** 24-hour window anomaly detection

**Architecture:**
- Embedding dimension: 3
- GRU hidden dimension: 64
- Number of experts: 3
- Probabilistic Label Enhancement

**Features:** 7 features

**Window:** 1440 timesteps (24 hours at 1 min intervals)

**File:** `models/enhanced/ple_gru.pth`

---

### 3. Hybrid Fusion

**Purpose:** Combine MSIF-LSTM and PLE-GRU scores

**Methods:**
- `weighted_ensemble` - Weighted average
- `max_ensemble` - Maximum of both
- `rule_based_fallback` - Rule-based scoring (default)

**Weights:**
```python
RULE_BASED_WEIGHTS = {
    'status_5xx': 0.40,
    'high_error': 0.30,
    'slow_response': 0.20,
    'high_cpu': 0.10,
    'high_memory': 0.10,
}
```

---

### Severity Levels

| Score Range | Severity |
|-------------|----------|
| 0.80 - 1.00 | CRITICAL |
| 0.60 - 0.79 | HIGH |
| 0.40 - 0.59 | MEDIUM |
| 0.20 - 0.39 | LOW |
| 0.00 - 0.19 | NORMAL |

---

## Request/Response Examples

### Example 1: High Error Rate

**Request:**
```bash
curl -X POST http://localhost:9000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "response_time": 250,
    "status_code": 200,
    "cpu_usage": 45.0,
    "memory_usage": 60.0,
    "error_rate": 0.45,
    "request_count": 1000
  }'
```

**Response:**
```json
{
  "status": "success",
  "hybrid_score": 0.72,
  "msif_score": 0.648,
  "ple_score": 0.72,
  "severity": "HIGH",
  "fusion_method": "rule-based-fallback",
  "confidence": 0.6
}
```

---

### Example 2: Server Error

**Request:**
```bash
curl -X POST http://localhost:9000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "response_time": 5200,
    "status_code": 500,
    "cpu_usage": 95.0,
    "memory_usage": 90.0,
    "error_rate": 0.35,
    "request_count": 500
  }'
```

**Response:**
```json
{
  "status": "success",
  "hybrid_score": 0.9,
  "msif_score": 0.81,
  "ple_score": 0.9,
  "severity": "CRITICAL",
  "fusion_method": "rule-based-fallback",
  "confidence": 0.6
}
```

---

### Example 3: Normal Request

**Request:**
```bash
curl -X POST http://localhost:9000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "response_time": 125,
    "status_code": 200,
    "cpu_usage": 35.0,
    "memory_usage": 45.0,
    "error_rate": 0.01,
    "request_count": 1500
  }'
```

**Response:**
```json
{
  "status": "success",
  "hybrid_score": 0.04,
  "msif_score": 0.036,
  "ple_score": 0.04,
  "severity": "NORMAL",
  "fusion_method": "rule-based-fallback",
  "confidence": 0.6
}
```

---

### Example 4: Multimodal Prediction

**Request:**
```bash
curl -X POST http://localhost:9000/predict/multimodal \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": 0.8,
    "logs": 0.6,
    "traces": 0.9
  }'
```

**Response:**
```json
{
  "status": "ANOMALY",
  "final_score": 0.88,
  "details": {
    "msif_score": 0.85,
    "ple_score": 0.82,
    "fusion_method": "weighted_ensemble",
    "model_agreement": 0.03
  }
}
```

---

## Configuration

### Environment Variables

Create a `.env` file in `ml-service/`:

```bash
# Service
SERVICE_NAME=ml-anomaly-detection
VERSION=1.0.0
PORT=9000

# Model paths
MODELS_PATH=./models
MSIF_MODEL_PATH=./models/enhanced/msif_lstm.pth
PLE_MODEL_PATH=./models/enhanced/ple_gru.pth

# Fusion settings
MSIF_WEIGHT=0.6
PLE_WEIGHT=0.4
FUSION_THRESHOLD=0.7

# Device
DEVICE=cpu  # or cuda
```

### config/settings.py

```python
SERVICE_NAME = "ml-anomaly-detection"
VERSION = "1.0.0"

# MSIF-LSTM settings
MSIF_WINDOW_SIZE = 60
MSIF_FEATURES = 5
MSIF_WEIGHT = 0.6

# PLE-GRU settings
PLE_WINDOW_SIZE = 1440
PLE_FEATURES = 7
PLE_WEIGHT = 0.4

# Fusion
FUSION_THRESHOLD = 0.7

# Device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

---

## Training

### Train MSIF-LSTM

```powershell
cd ml-service/training/fusion
python train_msif_enhanced.py
```

### Train PLE-GRU

```powershell
cd ml-service/training/fusion
python train_ple_enhanced.py
```

### Train Encoders

```powershell
cd ml-service/training/pretrain
python train_metric_encoder.py
python train_log_encoder.py
python train_trace_encoder.py
```

---

## Building & Running

### Install Requirements

```powershell
pip install -r requirements.txt
```

### Run in Development

```powershell
python api/app_multimodal.py
```

### Run with Gunicorn

```powershell
gunicorn -w 2 -b 0.0.0.0:9000 api.app:app
```

### Build Docker Image

```powershell
docker build -t ml-service .
```

### Run Docker Container

```powershell
docker run -d -p 9000:9000 ml-service
```

---

## Integration with Backend

### Backend Configuration

In `backend-service/src/main/resources/application.yml`:

```yaml
python:
  service:
    url: http://localhost:9000
    enabled: true
    timeout: 30
```

### Backend API Call

The backend calls the ML service at `/predict`:

```python
import requests

response = requests.post(
    "http://localhost:9000/predict",
    json={
        "response_time": 2500,
        "status_code": 500,
        "cpu_usage": 85.0,
        "memory_usage": 70.0,
        "error_rate": 0.15,
        "request_count": 1500
    }
)

result = response.json()
print(result["hybrid_score"])  # 0.72
print(result["severity"])       # HIGH
```

---

## Troubleshooting

### Issue: Port 9000 Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr 9000

# Kill process or change port in app_multimodal.py
# app.run(host="0.0.0.0", port=9001, debug=False)
```

---

### Issue: Model Weights Not Found

**Error:**
```
⚠️ MSIF-LSTM weights not found at models/enhanced/msif_lstm.pth
```

**Solution:**
1. Train the models first:
```powershell
cd ml-service/training/fusion
python train_msif_enhanced.py
python train_ple_enhanced.py
```

2. Or use rule-based fallback (default behavior)

---

### Issue: CUDA Not Available

**Error:**
```
RuntimeError: CUDA out of memory
```

**Solution:**
- Use CPU instead:
```python
DEVICE = torch.device("cpu")
```

- Or set in environment:
```bash
export CUDA_VISIBLE_DEVICES=""
```

---

### Issue: Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'torch'
```

**Solution:**
```powershell
pip install torch numpy pandas scikit-learn flask
```

---

### Issue: TensorFlow/Keras Model Loading Error

**Error:**
```
ValueError: Unknown layer: KerasTensor
```

**Solution:**
- Use PyTorch models (`.pth` files) instead of TensorFlow (`.h5` files)
- Or retrain models with compatible TensorFlow version

---

### Issue: High Latency

**Solution:**
- Use GPU acceleration if available
- Reduce model complexity
- Use batch prediction

---

## Common Commands

### Test Health

```bash
curl http://localhost:9000/health
```

### Test Prediction

```bash
curl -X POST http://localhost:9000/predict \
  -H "Content-Type: application/json" \
  -d '{"response_time": 250, "status_code": 500, "cpu_usage": 85}'
```

### Get Model Info

```bash
curl http://localhost:9000/api/model-info
```

### View Logs

```powershell
docker logs ml-container
```

---

## Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| flask | >=2.3.0 | Web framework |
| flask-cors | >=4.0.0 | CORS support |
| gunicorn | >=21.0.0 | Production server |
| torch | latest | Deep learning |
| tensorflow | >=2.16.0 | Additional ML |
| numpy | >=1.24.0 | Numerical computing |
| pandas | >=2.0.0 | Data processing |
| scikit-learn | >=1.3.0 | ML utilities |

### Monitoring

| Package | Purpose |
|---------|---------|
| prometheus-client | Metrics |
| python-json-logger | Logging |

---

## Quick Reference

### Start Service

```powershell
cd ml-service/api
python app_multimodal.py
```

### Access URL

```
http://localhost:9000
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/predict` | Main prediction |
| POST | `/predict/multimodal` | Multi-source |
| POST | `/predict/test` | Test endpoint |
| GET | `/api/model-info` | Model info |

### Severity Levels

| Score | Severity |
|-------|----------|
| 0.80+ | CRITICAL |
| 0.60+ | HIGH |
| 0.40+ | MEDIUM |
| 0.20+ | LOW |
| <0.20 | NORMAL |

### Rule-Based Weights

| Condition | Weight |
|-----------|--------|
| status >= 500 | 0.40 |
| error_rate > 30% | 0.30 |
| response_time > 1s | 0.20 |
| cpu > 80% | 0.10 |
| memory > 85% | 0.10 |