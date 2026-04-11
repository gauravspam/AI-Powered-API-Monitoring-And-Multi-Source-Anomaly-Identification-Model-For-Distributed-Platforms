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
                                │
                                ▼
                         ┌─────────────────┐
                         │  PostgreSQL     │
                         │  (Docker)       │
                         └─────────────────┘
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
   - Multimodal anomaly detection API
   - Flask/FastAPI based service
   - Integration with backend via HTTP client

4. **Infrastructure**
   - Docker Compose configuration
   - PostgreSQL container setup
   - OpenSearch (optional, disabled by default)
   - Fluentd logging (optional)

### Recently Completed Changes

- **PostgreSQL Port Fix**: Updated `application.yml` to use port 5433 instead of 5432 to match the Docker container configuration
- **Fluentd Configuration**: Enabled fluentd logging (previously disabled)
- **Multiple Files**: Pushed 55 files including backend controllers, frontend components, infrastructure configs, and utility scripts

## Running the Project

### Prerequisites

- Java 17+
- Node.js 18+
- Python 3.8+
- Docker & Docker Compose
- WSL (for Docker on Windows)

### Quick Start Commands

#### 1. Start Database (PostgreSQL via Docker in WSL)

```bash
# In WSL terminal
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

# Option A: Just run (now works with port 5433)
./gradlew bootRun

# Option B: With docker profile (if using docker-compose)
./gradlew bootRun --args="--spring.profiles.active=docker"
```

#### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

#### 4. Start ML Service

```bash
cd ml-service/api
pip install -r requirements.txt
python app_multimodal.py
```

### Docker Compose (Alternative)

```bash
cd infrastructure/docker
docker-compose up -d
```

## Configuration Files

### Key Configuration Files

| File | Purpose |
|------|---------|
| `backend-service/src/main/resources/application.yml` | Main Spring Boot config (DB, JPA, logging) |
| `backend-service/src/main/resources/application-docker.yml` | Docker profile config with env variables |
| `backend-service/build.gradle` | Gradle build configuration |
| `frontend/vite.config.js` | Vite bundler configuration |
| `frontend/src/api/http.js` | Axios HTTP client setup |
| `infrastructure/docker/docker-compose.yml` | Docker services configuration |

### Important Configurations

**PostgreSQL Connection** (application.yml):
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5433/api_monitoring
    username: api_monitor
    password: api_monitor_pwd
```

**Backend API Base URL** (frontend/.env):
```
VITE_API_URL=http://localhost:8080/api
```

## Project Structure

```
.
├── backend-service/          # Spring Boot application
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/api/monitoring/backend/
│   │   │   │   ├── config/      # Configuration classes
│   │   │   │   ├── controller/  # REST controllers
│   │   │   │   ├── dto/         # Data transfer objects
│   │   │   │   ├── model/       # Entity models
│   │   │   │   └── repository/  # JPA repositories
│   │   │   └── resources/
│   │   │       ├── application.yml
│   │   │       ├── application-docker.yml
│   │   │       ├── logback-spring.xml
│   │   │       └── db/migration/ # Flyway migrations
│   │   └── test/
│   └── build.gradle
│
├── frontend/                 # React application
│   ├── src/
│   │   ├── api/             # HTTP client
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts
│   │   ├── pages/          # Page components
│   │   └── main.jsx        # Entry point
│   ├── package.json
│   └── vite.config.js
│
├── ml-service/              # Python ML service
│   ├── api/
│   │   ├── app_multimodal.py
│   │   └── requirements.txt
│   └── docs/
│
└── infrastructure/          # Infrastructure configs
    └── docker/
        └── docker-compose.yml
```

## Known Issues & Solutions

### 1. PostgreSQL Connection Error

**Problem**: Backend fails to start with connection refused to PostgreSQL

**Solution**: 
- Ensure PostgreSQL container is running on port 5433
- Run: `docker ps` to check container status
- Restart container if needed: `docker restart <container-name>`

### 2. Port Already in Use

**Problem**: Error message about port 8080 or 5433 already in use

**Solution**:
- Find process: `netstat -ano | findstr 8080` (Windows)
- Kill process or change port in application.yml

### 3. Frontend CORS Errors

**Problem**: Browser blocks API calls to backend

**Solution**:
- Check CORS configuration in CorsConfig.java
- Ensure backend is running on correct port

### 4. ML Service Not Responding

**Problem**: Backend can't connect to ML service

**Solution**:
- Verify ML service is running: `curl http://localhost:9000`
- Check ML_SERVICE_URL in application.yml

## In Progress Tasks

1. **Full System Integration Testing**
   - Test all REST API endpoints
   - Verify data flow between components
   - End-to-end anomaly detection workflow

2. **Frontend-backend Integration**
   - Verify all pages load correctly
   - Test authentication flow
   - Confirm data displays properly

3. **Database Migrations**
   - Flyway migration V2 for environment column in system_metrics

## GPU Training

### Prerequisites

Before training the ML models, ensure your system has:

1. **NVIDIA GPU** with CUDA compute capability 3.5+
2. **CUDA Toolkit** 11.8 or later
3. **cuDNN** 8.x or later
4. **PyTorch with CUDA** support

### Install PyTorch with CUDA

```bash
# Install PyTorch with CUDA 11.8 support (recommended for most GPUs)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or for CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Training Scripts

All training scripts are located in `ml-service/training/`:

| Script | Purpose | Data Source |
|--------|---------|-------------|
| `pretrain/train_metric_encoder.py` | Pre-train metric encoder | `data/raw/smd/train/` (SMD dataset) |
| `pretrain/train_log_encoder.py` | Pre-train log encoder (BERT) | `data/raw/loghub/HDFS.log` |
| `pretrain/train_trace_encoder.py` | Pre-train trace encoder | `data/raw/deathstar/flat_csv/` |
| `fusion/train_msif_enhanced.py` | Train MSIF-LSTM fusion model | `data/raw/train_ticket/AIOps挑战赛数据/2020_04_11/` |
| `fusion/train_ple_enhanced.py` | Train PLE-GRU fusion model | `data/raw/train_ticket/AIOps挑战赛数据/2020_04_11/` |

### Training Commands

```bash
cd ml-service

# Install dependencies
pip install -r requirements.txt

# 1. Pre-train Metric Encoder (~5-10 minutes on GPU)
python training/pretrain/train_metric_encoder.py

# 2. Pre-train Log Encoder (~10-20 minutes on GPU, requires BERT)
python training/pretrain/train_log_encoder.py

# 3. Pre-train Trace Encoder (~5-10 minutes on GPU)
python training/pretrain/train_trace_encoder.py

# 4. Train MSIF-LSTM Fusion Model (~10-15 minutes on GPU)
python training/fusion/train_msif_enhanced.py

# 5. Train PLE-GRU Fusion Model (~10-15 minutes on GPU)
python training/fusion/train_ple_enhanced.py
```

### Expected Training Time

| Model | GPU Training Time | CPU Training Time |
|-------|-------------------|-------------------|
| Metric Encoder | ~5-10 min | ~30-60 min |
| Log Encoder (BERT) | ~10-20 min | ~2-4 hours |
| Trace Encoder | ~5-10 min | ~30-60 min |
| MSIF-LSTM | ~10-15 min | ~1-2 hours |
| PLE-GRU | ~10-15 min | ~1-2 hours |
| **Total** | ~40-60 min | ~5-8 hours |

### Model Output Locations

Trained models are saved to:

- `ml-service/models/encoders/metric/metric_encoder_pretrained.pth`
- `ml-service/models/encoders/log/log_encoder.pth`
- `ml-service/models/encoders/trace/trace_encoder.pth`
- `ml-service/models/enhanced/msif_lstm.pth`
- `ml-service/models/enhanced/ple_gru.pth`

### Verifying Training Results

After training, test the ML service:

```bash
# Test multimodal endpoint with high anomaly values
curl -X POST http://localhost:9000/predict/multimodal \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {"cpu_usage": 95, "memory_usage": 90, "error_rate": 5.0},
    "logs": [{"level": "ERROR", "message": "Connection timeout"}],
    "traces": [{"service": "api-gateway", "duration": 5000, "success": false}]
  }'

# Expected: Higher anomaly score (0.7-0.95) instead of ~1e-07
```

### Sample Data Generation

If you don't have the original datasets, the training scripts will automatically generate synthetic data for training. However, for best results:

1. **SMD Dataset** (for Metric Encoder): Download from [Server Machine Dataset](https://github.com/China-UK-ZeroTrust/AI-MOps)
2. **HDFS Logs** (for Log Encoder): Download from [Loghub](https://github.com/logpai/loghub)
3. **DeathStarBench** (for Trace Encoder): Download from [DeathStarBench](https://github.com/cs-au-dc/DeathStarBench)
4. **AIOps Challenge Data**: Use provided data in `data/raw/train_ticket/`

## Next Tasks (Priority Order)

### High Priority
1. Verify backend starts with `.\gradlew bootRun` (no extra args needed now)
2. Test all API endpoints: /api/metrics, /api/logs, /api/traces, /api/anomalies, /api/overview
3. Verify PostgreSQL database connection and schema

### Medium Priority
4. Start frontend with `npm run dev` and verify all pages
5. Start ML service and test anomaly detection
6. Test authentication flow

### Lower Priority
7. Configure and test Fluentd logging if needed
8. Enable OpenSearch if log aggregation is required
9. Performance testing and optimization

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/metrics | Get all metrics |
| GET | /api/logs | Get all logs |
| GET | /api/traces | Get all traces |
| GET | /api/anomalies | Get all anomalies |
| GET | /api/overview | Get dashboard overview |
| POST | /api/metrics | Create new metric |
| POST | /api/logs | Create new log entry |
| POST | /api/traces | Create new trace |
| DELETE | /api/anomalies/{id} | Delete anomaly |
| GET | /actuator/health | Health check |

## Database Schema

### Tables
- **metrics**: API performance metrics (response time, status codes)
- **logs**: Application logs
- **traces**: Distributed tracing data
- **anomalies**: Detected anomalies with scores
- **system_metrics**: System-level metrics with environment column

## Environment Variables

### Backend
- `SPRING_PROFILES_ACTIVE`: Active Spring profile (default, docker)
- `POSTGRES_HOST`: Database host
- `POSTGRES_PORT`: Database port
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password

### Frontend
- `VITE_API_URL`: Backend API URL

### ML Service
- `ML_SERVICE_PORT`: Service port (default 9000)

## Troubleshooting Commands

```bash
# Check Docker containers
docker ps -a

# View backend logs
tail -f backend-service/logs/backend-service.log

# Check PostgreSQL connection
docker exec -it <postgres-container> psql -U api_monitor -d api_monitoring

# Rebuild backend
cd backend-service && ./gradlew clean build

# Rebuild frontend
cd frontend && npm run build

# View all running processes
docker-compose ps
```

## Useful Development Tips

1. **Hot Reload**: Backend supports hot reload, frontend uses Vite's HMR
2. **Database Console**: Access via Spring Boot Actuator or DBeaver
3. **API Testing**: Use Postman or curl to test endpoints before frontend integration
4. **Logging**: Check `backend-service/logs/backend-service.log` for issues

## Contributing

When continuing development:
1. Create a new branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Run lint/typecheck before committing
4. Push and create PR to main

## Notes

- This file should be updated as project progresses
- Last updated: April 2026
- PostgreSQL runs on non-standard port 5433 (mapped from container's 5432)
- Docker runs via WSL on Windows
- Backend uses Gradle, not Maven (pom.xml was removed)