# AI-Powered API Monitoring - Project Continuation Guide

## Project Overview

This is an AI-powered API monitoring and multi-source anomaly identification model for distributed platforms. The system consists of three main components:

- **Backend Service**: Spring Boot (Java) REST API for monitoring
- **Frontend**: React + Vite web interface
- **ML Service**: Python-based anomaly detection service

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  Backend API    │────▶│  ML Service     │
│   (React/Vite)  │     │ (Spring Boot)   │     │ (Python)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                      │
                                ▼                      ▼
                         ┌─────────────────┐     ┌─────────────────┐
                         │  PostgreSQL     │     │ Encoders+Models │
                         │  (Docker)       │     │ GPU Training    │
                         └─────────────────┘     └─────────────────┘
```

## Current Project Status

### Completed Features

1. **Backend Service (Spring Boot)**
   - REST API endpoints for metrics, logs, traces, anomalies, and overview
   - PostgreSQL database integration with JPA/Hibernate
   - CORS configuration for frontend integration
   - Flyway database migrations
   - Logging with logback-spring.xml
   - Health check endpoints via Spring Actuator

2. **Frontend (React + Vite)**
   - Authentication context with login functionality
   - HTTP client configuration with axios
   - Alert list component
   - Models page
   - Vite configuration with proxy setup

3. **ML Service (Python)**
   - ✅ Multimodal anomaly detection API
   - ✅ Flask/FastAPI based service
   - ✅ Integration with backend via HTTP client
   - ✅ Trained MSIF-LSTM model (F1: 90%)
   - ✅ Trained PLE-GRU model (F1: 92.6%)

4. **Infrastructure**
   - Docker Compose configuration
   - PostgreSQL container setup

## Trained ML Models

### Model Performance

| Model | Best F1 Score | Notes |
|-------|---------------|-------|
| MSIF-LSTM | **90%** | Bidirectional LSTM with Attention |
| PLE-GRU | **92.6%** | Progressive Learning Enhancement |

### Training Details

- **Dataset**: AIOps 2020 Challenge (train-ticket microservice)
- **Training Samples**: ~2500 sequences
- **Anomaly Rate**: ~5.8% (144 anomalies)
- **Training Hardware**: NVIDIA GTX 1660 Super (6GB VRAM)
- **Training Epochs**: 60 epochs
- **Key Fix**: UTC+8 timezone alignment

### Model Files

```
ml-service/models/enhanced/
├── metric_encoder_aiops.pth   # TCN encoder (616KB)
├── msif_lstm_strict.pth       # MSIF-LSTM (12.3MB)
└── ple_gru_strict.pth         # PLE-GRU (28.8MB)
```

## Running the Project

### Prerequisites

- Java 17+
- Node.js 18+
- Python 3.8+
- Docker & Docker Compose
- NVIDIA GPU (optional, for training)

### Quick Start Commands

#### 1. Start Database (PostgreSQL via Docker)

```bash
docker run -d \
  --name postgres-api-monitor \
  -e POSTGRES_DB=api_monitoring \
  -e POSTGRES_USER=api_monitor \
  -e POSTGRES_PASSWORD=api_monitor_pwd \
  -p 5433:5432 \
  postgres:15
```

#### 2. Start Backend Service

```bash
cd backend-service
./gradlew bootRun
```

#### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

#### 4. Start ML Service

```bash
cd ml-service
.\venv\Scripts\python.exe api\app_multimodal.py
```

## GPU Training

### Install PyTorch with CUDA

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Verify CUDA

```python
import torch
print('CUDA available:', torch.cuda.is_available())
print('CUDA device:', torch.cuda.get_device_name(0))
```

### Training Commands

```bash
cd ml-service

# Train MSIF-LSTM (on GPU)
python train_aiops_fixed.py --model msif --epochs 60 --batch 16 --hidden 256 --lr 0.0005

# Train PLE-GRU (on GPU)
python train_aiops_fixed.py --model ple --epochs 60 --batch 16 --hidden 256 --lr 0.0005
```

### Expected Training Time

| Model | GPU Time | CPU Time |
|-------|----------|----------|
| MSIF-LSTM | ~2 min | ~30 min |
| PLE-GRU | ~2 min | ~30 min |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/metrics | Get all metrics |
| GET | /api/logs | Get all logs |
| GET | /api/traces | Get all traces |
| GET | /api/anomalies | Get all anomalies |
| GET | /api/overview | Get dashboard overview |
| POST | /api/detect | ML anomaly detection |
| GET | /actuator/health | Health check |

## Testing ML Service

```bash
# Test anomaly detection
curl -X POST http://localhost:9000/detect \
  -H "Content-Type: application/json" \
  -d '{
    "log": "ERROR Connection timeout to database",
    "metrics": [95, 90, 5.0],
    "trace": [5000, false]
  }'
```

Expected response:
```json
{
  "anomaly": true,
  "score": 0.85,
  "severity": "HIGH"
}
```

## Configuration Files

| File | Purpose |
|------|---------|
| `backend-service/src/main/resources/application.yml` | Main Spring Boot config |
| `frontend/vite.config.js` | Vite bundler configuration |
| `ml-service/train_aiops_fixed.py` | ML training script |
| `ml-service/api/app_multimodal.py` | ML service API |

## Troubleshooting

### PostgreSQL Connection Error

```bash
# Check container status
docker ps

# Restart if needed
docker restart postgres-api-monitor
```

### ML Service Not Responding

```bash
# Verify ML service is running
curl http://localhost:9000/health

# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

### Model Training Issues

If training fails to detect anomalies:
1. Check timestamp alignment (UTC+8 timezone)
2. Verify fault labels match business metrics timestamps
3. Ensure proper positive weight for class imbalance

## Known Issues & Solutions

1. **Timestamp Alignment**: Business metrics use UTC, fault labels are UTC+8. Fixed in `train_aiops_fixed.py`
2. **Class Imbalance**: 5.8% anomaly rate. Fixed with weighted BCE loss
3. **Early Stopping**: May stop too early. Use more epochs with lower learning rate

## Project Structure

```
.
├── backend-service/          # Spring Boot application
│   ├── src/main/java/com/api/monitoring/backend/
│   └── src/main/resources/
│       ├── application.yml
│       └── application-docker.yml
│
├── frontend/                 # React application
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── pages/
│   └── package.json
│
├── ml-service/              # Python ML service
│   ├── api/
│   │   ├── app_multimodal.py    # Main API
│   │   └── requirements.txt
│   ├── models/
│   │   └── enhanced/           # Trained models
│   │       ├── msif_lstm_strict.pth
│   │       └── ple_gru_strict.pth
│   ├── train_aiops_fixed.py    # Training script
│   └── venv/                   # Virtual environment
│
├── NEXT_STEPS.md            # Implementation roadmap
├── PROJECT_CONTINUATION.md  # This file
└── infrastructure/
    └── docker/
        └── docker-compose.yml
```

## Contributing

When continuing development:
1. Create a new branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Run lint/typecheck before committing
4. Push and create PR to main

## Notes

- This file should be updated as project progresses
- PostgreSQL runs on port 5433 (mapped from container's 5432)
- GPU training requires PyTorch with CUDA support
- Models achieve ~90% F1 on AIOps 2020 dataset
- Target 96% requires more labeled data or better feature engineering

---

*Last Updated: 2026-04-14*

*ML Models Trained and Functional*
