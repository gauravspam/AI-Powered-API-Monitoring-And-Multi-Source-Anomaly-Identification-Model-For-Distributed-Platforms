# AI-Powered API Monitoring & Multi-Source Anomaly Detection System

<div align="center">

![Project Banner](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)
![Java](https://img.shields.io/badge/Java-17+-red?style=flat-square)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square)

**Enterprise-grade API monitoring and anomaly detection platform for distributed microservices**

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Documentation](#-documentation)

</div>

---

## 📋 Table of Contents

- [Project Idea](#-project-idea)
- [Features](#-features)
- [Architecture & Data Flow](#-architecture--data-flow)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start with Docker](#-quick-start-with-docker)
- [Manual Setup](#-manual-setup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Infrastructure Setup](#infrastructure-setup)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)

---

## 💡 Project Idea

### Problem Statement
Microservices architectures generate massive volumes of API traffic across distributed systems. Detecting anomalies in real-time—such as:
- **Performance degradation** (slow response times)
- **Traffic anomalies** (unusual request patterns)
- **Error rate spikes** (sudden increases in failures)
- **Resource exhaustion** (high CPU/memory usage)

...remains a critical challenge for DevOps and SRE teams.

### Solution
This project builds an **intelligent, multi-source anomaly detection system** that:
- **Aggregates data** from multiple sources (APIs, logs, metrics, distributed traces)
- **Applies ML models** (Isolation Forest, LSTM, Statistical Analysis) for real-time anomaly detection
- **Visualizes insights** through an interactive dashboard
- **Triggers alerts** when anomalies are detected
- **Enables root-cause analysis** through correlated data streams

### Key Objectives
✅ Real-time monitoring of distributed API endpoints  
✅ Multi-algorithm anomaly detection (statistical + ML-based)  
✅ Intelligent correlation of anomalies across multiple data sources  
✅ Scalable architecture for enterprise deployments  
✅ Easy integration with existing microservices  

---

## 🎯 Features

### Core Monitoring
- ✨ **Real-Time API Monitoring** - Track API performance, latency, error rates across distributed platforms
- 📊 **Multi-Source Anomaly Detection** - Detect anomalies from APIs, logs, metrics, and traces simultaneously
- 🤖 **ML-Powered Analysis** - Ensemble ML models (Isolation Forest, LSTM, Statistical methods)
- 🔗 **Intelligent Correlation** - Link related anomalies across multiple data sources
- 📈 **Performance Metrics** - Throughput, latency, error rates, success rates

### Dashboard & Visualization
- 🎨 **Interactive Dashboard** - Real-time visualization of API metrics and anomalies
- 📉 **Historical Analytics** - Trend analysis and pattern recognition over time
- 🔍 **Root Cause Analysis** - Drill-down capabilities to identify anomaly origins
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile devices

### Advanced Features
- 🚨 **Smart Alerting** - Configurable alerts with multiple notification channels
- 🔐 **Enterprise Security** - Role-based access control and data encryption
- 📦 **Scalable Architecture** - Horizontally scalable components with Docker
- 🔌 **API Extensibility** - REST APIs for custom integrations
- 💾 **Data Persistence** - Multi-database support (PostgreSQL, MongoDB)

---

## 🏗️ Architecture & Data Flow

### System Architecture

![System Architecture Diagram](https://agi-prod-file-upload-public-main-use1.s3.amazonaws.com/8836b905-4a88-4d40-83e6-065f7bc53dd1)

**Architecture Components Overview:**

1. **Sources** - Multiple data sources including APIs, SaaS services, cloud-native services, and logs
2. **Secret Injection** - Agent-based injection system (HashiCorp Vault integration)
3. **Collector Agent Layer** - Fluent Bit for on-premises and cloud/SaaS environments
4. **Control Log Aggregation** - Fluentd for centralized log collection
5. **Log & Metric Storage** - OpenSearch for log storage and PostgreSQL for metadata/config
6. **Logs, Metrics & Traces** - Aggregated data from multiple sources
7. **Retraining** - Continuous model improvement with feedback loop
8. **Anomaly Scores** - Multi-model approach (MSIF-LSTM, PLE-GRU) for anomaly detection
9. **OpenSearch Dashboard** - Visualization and exploration
10. **Alerts & Incident Response** - Alert generation and incident management
11. **Notification Channels** - Slack, PagerDuty, Email for alerts

### Data Flow Diagram

```
                    REQUEST INGESTION
                           │
                    ┌──────▼──────┐
                    │  Collector  │ (Java)
                    │  Microservice
                    └──────┬──────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
    ┌────▼─────┐    ┌──────▼──────┐   ┌──────▼──────┐
    │Prometheus │    │   ELK/Logs  │   │  Traces    │
    │Metrics    │    │             │   │ (Jaeger)   │
    └────┬─────┘    └──────┬──────┘   └──────┬──────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Time-Series │ (PostgreSQL)
                    │   Database  │
                    └──────┬──────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
    ┌────▼─────┐    ┌──────▼──────┐   ┌──────▼──────┐
    │Statistical│   │Isolation    │   │  LSTM       │
    │Model      │   │Forest       │   │  Model      │
    └────┬─────┘    └──────┬──────┘   └──────┬──────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │Correlation  │ (Python)
                    │ Engine      │
                    └──────┬──────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
    ┌────▼─────┐    ┌──────▼──────┐   ┌──────▼──────┐
    │Alerts    │    │ Storage     │   │  REST API   │
    │Queue     │    │ (PostgreSQL)│   │             │
    └────┬─────┘    └──────┬──────┘   └──────┬──────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Frontend   │ (React)
                    │  Dashboard   │
                    └─────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Data Collector** | Java, Spring Boot | Aggregates data from multiple sources; REST endpoints for ingestion |
| **Processing Engine** | Python, NumPy, Scikit-learn | Runs anomaly detection algorithms on streaming data |
| **ML Models** | TensorFlow/PyTorch | Statistical, Isolation Forest, LSTM for anomaly detection |
| **Time-Series DB** | PostgreSQL, InfluxDB | Stores metrics and events with high-throughput writes |
| **Message Queue** | Kafka/RabbitMQ | Handles asynchronous data flow between components |
| **Frontend** | React, Redux | Interactive dashboard for visualization and alerting |
| **Log Aggregation** | Fluentd, OpenSearch | Centralized logging and search |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Java 17, Spring Boot, Spring Data JPA, PostgreSQL |
| **ML/Data Processing** | Python 3.9+, TensorFlow, Scikit-learn, Pandas, NumPy |
| **Frontend** | React 18, Redux, Axios, Chart.js, Tailwind CSS |
| **Databases** | PostgreSQL (primary), InfluxDB (time-series), MongoDB (logs) |
| **Messaging** | Apache Kafka / RabbitMQ |
| **Log Aggregation** | Fluentd, OpenSearch |
| **Monitoring** | Prometheus, Grafana, ELK Stack |
| **Containerization** | Docker, Docker Compose |
| **Deployment** | CI/CD with GitHub Actions |

---

## 📦 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows (WSL2 recommended)
- **CPU**: Minimum 4 cores (8+ recommended for full deployment)
- **RAM**: Minimum 8GB (16GB+ recommended)
- **Disk**: 20GB free space for Docker images and data

### Required Software

#### For Docker Deployment (Recommended)
- **Docker**: v20.10+
- **Docker Compose**: v2.0+

#### For Manual Setup
- **Java**: JDK 17 or later
- **Python**: 3.9 or later
- **Node.js**: 16+ with npm/yarn
- **PostgreSQL**: 14+
- **Git**: 2.30+

### Installation Commands

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y \
  docker.io docker-compose git curl wget \
  openjdk-17-jdk python3.9 python3-pip nodejs npm
```

**macOS:**
```bash
brew install docker docker-compose git openjdk@17 python@3.9 node
```

**Windows (WSL2):**
Use WSL2 Ubuntu environment and follow Ubuntu installation steps.

---

## 🚀 Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/gauravspam/AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms.git

cd AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms
```

### 2. Configure Environment Variables

Copy environment templates and customize:

```bash
# Backend configuration
cp backend/.env.example backend/.env

# Frontend configuration
cp frontend/.env.example frontend/.env

# Infrastructure configuration
cp infrastructure/.env.example infrastructure/.env
```

Edit each `.env` file with your specific configuration (database URLs, API keys, etc.)

### 3. Start All Services with Docker Compose

```bash
# Start all services (background mode)
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ml-engine
```

### 4. Verify Services

```bash
# Check all containers are running
docker-compose ps

# Test backend API
curl http://localhost:8080/api/health

# Test frontend
# Open browser: http://localhost:3000
```

### 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## 🔧 Manual Setup

### Backend Setup

#### Prerequisites
- Java JDK 17+
- Maven 3.8+
- PostgreSQL 14+

#### Step 1: Navigate to Backend Directory

```bash
cd backend
```

#### Step 2: Configure Database

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE api_monitoring;"

# Configure database connection in backend/.env
DATABASE_URL=jdbc:postgresql://localhost:5432/api_monitoring
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
```

#### Step 3: Build Backend

```bash
# Build with Maven
mvn clean package -DskipTests

# Or with gradle
gradle clean build -x test
```

#### Step 4: Run Backend

```bash
# Development mode with hot reload
mvn spring-boot:run

# Production mode
java -jar target/api-monitoring-backend-1.0.0.jar
```

**Backend will start on**: `http://localhost:8080`

### Frontend Setup

#### Prerequisites
- Node.js 16+
- npm or yarn

#### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

#### Step 2: Install Dependencies

```bash
npm install
# or
yarn install
```

#### Step 3: Configure Environment

Edit `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
REACT_APP_ENV=development
```

#### Step 4: Start Development Server

```bash
# Development mode with hot reload
npm start

# Build for production
npm run build

# Serve production build
npm install -g serve
serve -s build
```

**Frontend will start on**: `http://localhost:3000`

### Infrastructure Setup

#### Python ML Engine Setup

```bash
cd infrastructure/ml-engine

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run ML service
python3 app.py
```

**ML Engine will start on**: `http://localhost:5000`

---

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)

```env
# Server Configuration
SERVER_PORT=8080
SERVER_SERVLET_CONTEXT_PATH=/api

# Database Configuration
DATABASE_URL=jdbc:postgresql://localhost:5432/api_monitoring
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password
DATABASE_DRIVER=org.postgresql.Driver

# Connection Pool
HIKARI_MAXIMUM_POOL_SIZE=20
HIKARI_MINIMUM_IDLE=5

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Kafka Configuration
KAFKA_BROKER_URL=localhost:9092
KAFKA_TOPIC_METRICS=api-metrics
KAFKA_TOPIC_LOGS=api-logs

# JWT Security
JWT_SECRET=your_jwt_secret_key_min_32_chars
JWT_EXPIRATION=86400000

# Logging
LOGGING_LEVEL=INFO
LOG_FILE=/var/log/api-monitoring/app.log
```

#### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
REACT_APP_ENV=development
REACT_APP_DEBUG=true
REACT_APP_THEME=light
```

#### ML Engine (.env)

```env
FLASK_APP=app.py
FLASK_ENV=development
ML_MODEL_PATH=/models
DATABASE_URL=postgresql://user:password@localhost:5432/api_monitoring
KAFKA_BROKER=localhost:9092
```

---

## ▶️ Running the Application

### Full Stack with Docker Compose

```bash
# One-command startup
docker-compose up -d

# Wait for services to be healthy (~60 seconds)
docker-compose ps

# Access services:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8080/api
# Adminer (DB): http://localhost:8081
```

### Individual Service Commands

```bash
# Backend only
docker-compose up -d backend postgres

# Frontend + Backend
docker-compose up -d frontend backend postgres

# Full stack with ML
docker-compose up -d

# With debug logs
docker-compose up --logs frontend backend ml-engine
```

### Health Checks

```bash
# Backend health
curl -s http://localhost:8080/api/health | jq

# Frontend status
curl -s http://localhost:3000 | head -20

# ML Engine status
curl -s http://localhost:5000/health | jq
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8080/api
```

### Authentication
All API endpoints (except `/auth/*`) require JWT token in header:
```bash
Authorization: Bearer your_jwt_token
```

### Key Endpoints

#### Health & Monitoring
```bash
# Health check
GET /health

# Metrics summary
GET /v1/metrics/summary

# Get anomalies
GET /v1/anomalies?start_time=2024-01-01&end_time=2024-01-02&severity=HIGH

# Get alerts
GET /v1/alerts?status=ACTIVE
```

#### API Integration
```bash
# Register API endpoint
POST /v1/apis/register
Content-Type: application/json
{
  "name": "User Service",
  "url": "http://user-service:8080",
  "description": "User management service"
}

# Send metrics
POST /v1/metrics/ingest
Content-Type: application/json
{
  "api_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "latency_ms": 125,
  "status_code": 200,
  "response_size": 2048
}
```

#### Analytics
```bash
# Get anomaly trends
GET /v1/analytics/anomaly-trends?period=7d

# Get performance metrics
GET /v1/analytics/performance?api_id=uuid&granularity=1h
```

See [API Contracts](./docs/API_CONTRACTS.md) for complete endpoint documentation.

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Compose Port Already in Use
```bash
# Find process using port 8080
lsof -i :8080

# Stop conflicting service
kill -9 <PID>

# Or use different port
docker-compose up -d -e BACKEND_PORT=8081
```

#### 2. Database Connection Failed
```bash
# Check PostgreSQL is running
docker-compose ps | grep postgres

# Verify credentials in .env
# Check database exists
docker-compose exec postgres psql -U postgres -l

# Create database if missing
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE api_monitoring;"
```

#### 3. Backend Service Not Starting
```bash
# Check logs
docker-compose logs backend | tail -50

# Rebuild container
docker-compose down backend
docker-compose build --no-cache backend
docker-compose up -d backend

# Check for Java process
docker-compose exec backend ps aux | grep java
```

#### 4. Frontend Blank Page
```bash
# Clear browser cache (Ctrl+Shift+Delete)
# Check frontend logs
docker-compose logs frontend | tail -50

# Rebuild frontend
docker-compose down frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

#### 5. ML Engine Not Processing
```bash
# Check Python service
docker-compose logs ml-engine | tail -50

# Verify Kafka connection
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check model files exist
docker-compose exec ml-engine ls -la /models/
```

### Performance Optimization

#### For Large-Scale Deployments
```bash
# Increase JVM heap
export JAVA_OPTS="-Xmx4g -Xms2g"

# Scale containers
docker-compose up -d --scale backend=3 --scale ml-engine=2

# Enable caching
docker-compose exec backend redis-cli FLUSHALL
```

#### Database Optimization
```bash
# Create indexes
docker-compose exec postgres psql -U postgres -d api_monitoring -f /scripts/create_indexes.sql

# Vacuum database
docker-compose exec postgres psql -U postgres -d api_monitoring -c "VACUUM FULL ANALYZE;"
```

### Getting Help

1. **Check Logs**: `docker-compose logs <service>`
2. **Verify Configuration**: Review `.env` files
3. **Test Connectivity**: `curl http://localhost:<port>/health`
4. **Check Resources**: `docker stats`
5. **Review Issues**: Open GitHub issues for known problems

---

## 📚 Additional Resources

- **[Project Overview](./docs/PROJECT_OVERVIEW.md)** - Detailed architecture and design decisions
- **[Backend README](./backend/README.md)** - Backend-specific setup and development
- **[Frontend README](./frontend/README.md)** - Frontend-specific setup and development
- **[Infrastructure README](./infrastructure/README.md)** - Deployment and infrastructure guides
- **[API Contracts](./docs/API_CONTRACTS.md)** - Complete API endpoint documentation

---

<div align="center">

**Built with ❤️ for the DevOps and SRE community**

⭐ If you find this project helpful, please star it on GitHub!

</div>