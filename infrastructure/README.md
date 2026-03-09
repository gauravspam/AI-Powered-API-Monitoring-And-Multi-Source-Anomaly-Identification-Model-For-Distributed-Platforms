# 🏗️ Infrastructure - Docker Deployment

Complete containerized deployment stack for API monitoring platform including PostgreSQL, OpenSearch, Fluentd, Spring Boot Backend, and React Frontend.

---

## 📋 Prerequisites

- **Docker 29.x** - `29.1.3` or higher
- **Docker Compose 2.39.x** - `2.39.1` or higher
- **Linux/macOS/Windows** with Docker installed
- Minimum **4GB RAM** for full stack
- Minimum **20GB disk space**

---

## 📚 Architecture

**Observability Strategy: Option B - Specialized Signal Pipelines**

This project implements a **hybrid observability architecture** where each signal type (logs, metrics, traces) flows through an optimized path:

```
┌───────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                          │
│     (Backend API, Frontend, ML Service, etc.)             │
└───────┬──────────────────────┬─────────────────────┬──────┘
        │                      │                     │
        │ Logs                 │ Metrics             │ Traces
        │ (JSON)               │ (JSON/REST)         │ (JSON/REST)
        ▼                      ▼                     ▼
   ┌─────────┐         ┌────────────┐        ┌────────────┐
   │Fluentd  │         │ Backend    │        │ Backend    │
   │ :24224  │         │ API        │        │ API        │
   │ :9880   │         │ /api/      │        │ /api/      │
   └────┬────┘         │ metrics    │        │ traces     │
        │              └──────┬─────┘        └──────┬─────┘
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐         ┌──────────────────────────────┐
   │OpenSearch│        │       PostgreSQL             │
   │  :9200  │         │ - systemmetrics              │
   │         │         │ - distributedtraces          │
   │ Logs    │         │ - apilogs                    │
   │ Storage │         │ - anomalydetections          │
   └─────────┘         └──────────┬───────────────────┘
                                  │
                                  ▼
                       ┌────────────────────┐
                       │   ML Service       │
                       │ Anomaly Detection  │
                       └────────────────────┘
```

### Signal Flow Summary

| Signal | Collector | Transport | Storage | Reason |
|--------|-----------|-----------|---------|---------|
| **Logs** | Fluentd | Forward/HTTP | OpenSearch | High-volume, full-text search |
| **Metrics** | Backend API | REST | PostgreSQL | Relational, ML-ready |
| **Traces** | Backend API | REST | PostgreSQL | Relational, correlation |

**See**: [📖 ARCHITECTURE_OPTION_B.md](../docs/ARCHITECTURE_OPTION_B.md) for complete details

---

## 📚 Architecture (Legacy)

```
Infrastructure Stack (Docker Compose)
│
├── Frontend Layer
│   └── api-monitoring-frontend (Nginx:Alpine on port 8080)
│
├── Backend Layer
│   └── api-monitoring-backend (Spring Boot 3.2.1 on port 8081)
│
├── Search & Logs
│   ├── opensearch (2.x on port 9200)
│   ├── opensearch-dashboards (on port 5601)
│   └── fluentd (on port 24224 TCP/UDP, 9880)
│
└── Data Storage
    ├── postgres (16.x on port 5432)
    └── volumes: opensearch-data, postgres-data, fluentd-buffer
```

---

## 🚀 Quick Start

### Clone & Navigate

```bash
git clone https://github.com/yourusername/AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms.git

cd AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms/infrastructure/docker
```

### Deploy Full Stack

```bash
# Start all services
docker compose up -d

# Wait for services to stabilize (60s)
echo "⏳ Waiting for services to start..."
sleep 60

# Check status
docker compose ps
```

### Verify Services

```bash
# Check all services are running
docker compose ps

# Test backend health
curl http://localhost:8081/actuator/health

# Test frontend
curl http://localhost:3000

# Test OpenSearch
curl http://localhost:9200

# Test Fluentd health
curl http://localhost:8888/healthcheck

# Test Fluentd metrics (Prometheus format)
curl http://localhost:24231/metrics
```

---

## 🧪 Testing the Data Pipelines

### 1. Test Log Ingestion (Fluentd → OpenSearch)

**Send a log via HTTP**:
```bash
curl -X POST http://localhost:9880/app.test \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test log from curl",
    "level": "INFO",
    "service": "test-service",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

**Verify in OpenSearch**:
```bash
# Search recent logs
curl -X GET "http://localhost:9200/logs-*/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match": {
        "message": "Test log from curl"
      }
    },
    "size": 10,
    "sort": [{"@timestamp": "desc"}]
  }'
```

**Check Fluentd buffer status**:
```bash
# Inspect buffer files
docker compose exec fluentd ls -lh /fluentd/log/

# View Fluentd logs
docker compose logs fluentd | tail -50
```

### 2. Test Metrics Ingestion (Backend API → PostgreSQL)

**Send a metric**:
```bash
curl -X POST http://localhost:8081/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "serviceName": "test-service",
    "cpuUsage": 45.2,
    "memoryUsage": 62.8,
    "diskIoBytes": 1048576,
    "networkIoBytes": 2097152,
    "responseTimeMs": 150,
    "requestCount": 1200,
    "errorRate": 0.02
  }'
```

**Verify in PostgreSQL**:
```bash
# Connect to database
docker compose exec postgres psql -U api_monitor -d api_monitoring

# Query recent metrics
SELECT id, service_name, cpu_usage_percent, memory_usage_percent, 
       response_time_ms, metric_timestamp 
FROM systemmetrics 
ORDER BY metric_timestamp DESC 
LIMIT 10;
```

### 3. Test Trace Ingestion (Backend API → PostgreSQL)

**Send a trace span**:
```bash
curl -X POST http://localhost:8081/api/traces/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "traceId": "test-trace-'$(date +%s)'",
    "spanId": "span-001",
    "serviceName": "test-service",
    "operationName": "GET /test",
    "startTime": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "endTime": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "duration": 123,
    "statusCode": 200,
    "tags": {
      "http.method": "GET",
      "http.url": "/test"
    }
  }'
```

**Verify in PostgreSQL**:
```bash
# Query recent traces
docker compose exec postgres psql -U api_monitor -d api_monitoring -c \
  "SELECT trace_id, span_id, service_name, operation_name, duration, start_time 
   FROM distributedtraces 
   ORDER BY start_time DESC 
   LIMIT 10;"
```

---

## 📊 Monitoring & Observability

### Fluentd Monitoring

**Health Check**:
```bash
curl http://localhost:8888/healthcheck
# Expected: 200 OK
```

**Prometheus Metrics**:
```bash
curl http://localhost:24231/metrics
# Metrics include:
# - fluentd_output_status_buffer_total_bytes
# - fluentd_output_status_retry_count
# - fluentd_output_status_emit_records
```

**Buffer Status**:
```bash
# Check buffer directory
docker compose exec fluentd du -sh /fluentd/log/*

# Watch buffer size in real-time
watch -n 2 'docker compose exec fluentd du -sh /fluentd/log/*'
```

### OpenSearch Monitoring

**Cluster Health**:
```bash
curl http://localhost:9200/_cluster/health?pretty
```

**Index Statistics**:
```bash
curl http://localhost:9200/_cat/indices/logs-*?v
```

**Count Logs**:
```bash
curl http://localhost:9200/logs-*/_count?pretty
```

### PostgreSQL Monitoring

**Table Sizes**:
```bash
docker compose exec postgres psql -U api_monitor -d api_monitoring -c \
  "SELECT 
     schemaname, 
     tablename, 
     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables 
   WHERE schemaname = 'public' 
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

**Record Counts**:
```bash
docker compose exec postgres psql -U api_monitor -d api_monitoring -c \
  "SELECT 
     'systemmetrics' AS table_name, COUNT(*) AS count FROM systemmetrics
   UNION ALL
   SELECT 'distributedtraces', COUNT(*) FROM distributedtraces
   UNION ALL
   SELECT 'apilogs', COUNT(*) FROM apilogs
   UNION ALL
   SELECT 'anomalydetections', COUNT(*) FROM anomalydetections;"
```

---

## 🔧 Configuration Files

### Fluentd Configuration

**Location**: `./fluent.conf`

**Key Settings**:
- Receives logs on ports 24224 (forward) and 9880 (HTTP)
- Buffers to `/fluentd/log/` for crash recovery
- Flushes to OpenSearch every 10 seconds or 5MB
- Creates daily indices: `logs-YYYY.MM.DD`
- Health check on port 8888
- Prometheus metrics on port 24231

**Edit and reload**:
```bash
# Edit configuration
nano ./fluent.conf

# Restart Fluentd to apply changes
docker compose restart fluentd

# Watch logs for errors
docker compose logs -f fluentd
```

### Backend Application Properties

**Location**: `../../backend-service/src/main/resources/application-docker.properties`

**Key Settings** (Docker profile):
```properties
# PostgreSQL
spring.datasource.url=jdbc:postgresql://postgres:5432/api_monitoring
spring.datasource.username=api_monitor
spring.datasource.password=api_monitor_pwd

# OpenSearch (for log queries via backend)
opensearch.enabled=true
opensearch.host=opensearch
opensearch.port=9200
opensearch.scheme=http
```

---

## 🚨 Troubleshooting

### Fluentd Not Receiving Logs

**1. Check Fluentd is running**:
```bash
docker compose ps fluentd
docker compose logs fluentd | tail -50
```

**2. Test connectivity**:
```bash
# Test HTTP input
curl -X POST http://localhost:9880/test \
  -H "Content-Type: application/json" \
  -d '{"message": "connectivity test"}'

# Check if port 24224 is listening
nc -zv localhost 24224
```

**3. Check buffer directory**:
```bash
docker compose exec fluentd ls -la /fluentd/log/
```

### OpenSearch Connection Issues

**1. Check OpenSearch health**:
```bash
curl http://localhost:9200/_cluster/health?pretty
```

**2. Check Fluentd → OpenSearch connectivity**:
```bash
# From Fluentd container
docker compose exec fluentd curl -v opensearch:9200
```

**3. Inspect OpenSearch logs**:
```bash
docker compose logs opensearch | grep -i error
```

### Metrics/Traces Not Appearing in PostgreSQL

**1. Check backend is running**:
```bash
curl http://localhost:8081/actuator/health
```

**2. Test API endpoint directly**:
```bash
curl -X POST http://localhost:8081/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "serviceName": "test",
    "cpuUsage": 50.0,
    "memoryUsage": 60.0
  }'
```

**3. Check backend logs**:
```bash
docker compose logs backend | grep -i error
```

**4. Verify database connection**:
```bash
docker compose exec postgres psql -U api_monitor -d api_monitoring -c "\dt"
```

### Container Resource Issues

**Check resource usage**:
```bash
docker stats

# Check disk usage
docker system df
```

**Clean up unused resources**:
```bash
# Remove stopped containers
docker compose down

# Remove unused images
docker image prune

# Remove unused volumes (CAUTION: data loss!)
docker volume prune
```

---

## 📖 Additional Resources

- **Architecture Guide**: [../docs/ARCHITECTURE_OPTION_B.md](../docs/ARCHITECTURE_OPTION_B.md)
- **API Contracts**: [../docs/api-contracts.md](../docs/api-contracts.md)
- **Fluentd Documentation**: https://docs.fluentd.org/
- **OpenSearch Documentation**: https://opensearch.org/docs/
- **Spring Boot Actuator**: https://docs.spring.io/spring-boot/docs/current/reference/html/actuator.html

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Start all services | `docker compose up -d` |
| Stop all services | `docker compose down` |
| View all logs | `docker compose logs -f` |
| Restart service | `docker compose restart <service>` |
| Send test log | `curl -X POST http://localhost:9880/test -d '{"message":"test"}'` |
| Send test metric | `curl -X POST http://localhost:8081/api/metrics -H "Content-Type: application/json" -d '{...}'` |
| Query OpenSearch | `curl http://localhost:9200/logs-*/_search?pretty` |
| Query PostgreSQL | `docker compose exec postgres psql -U api_monitor -d api_monitoring` |
| Fluentd health | `curl http://localhost:8888/healthcheck` |
| Fluentd metrics | `curl http://localhost:24231/metrics` |

---

### Verify Services

```bash
# Check all services are running
docker compose logs -f

# Test backend health
curl http://localhost:8081/health

# Test frontend
curl http://localhost:8080

# Test OpenSearch
curl -k -u admin:Str0ng@ApiMon#2025 https://localhost:9200
```

---

## 📦 Services Overview

| Service | Image | Port | Purpose | Signal Type |
|---------|-------|------|---------|-------------|
| **Frontend** | nginx:alpine | 3000 (host) → 80 | React dashboard UI | - |
| **Backend** | Spring Boot 3.2 | 8081 (host) → 8080 | REST API + Metrics/Traces ingestion | Metrics, Traces, Anomalies |
| **OpenSearch** | opensearchproject/opensearch:2.17 | 9200 | Log storage & search | Logs |
| **Fluentd** | Custom (v1.17) | 24224, 9880 | Log collector & shipper | Logs |
| **PostgreSQL** | postgres:16 | 5433 (host) → 5432 | Relational data store | Metrics, Traces, Anomalies |
| **Fake Server** | Node.js | 8082 | Mock API for testing | - |

### Fluentd Ports

- **24224** (TCP/UDP): Fluentd forward protocol (primary log ingestion)
- **9880**: HTTP input (alternative log ingestion)
- **24231**: Prometheus metrics (Fluentd monitoring)
- **8888**: Health check endpoint

### Data Flow Details

**Logs**:  
Services → Fluentd (:24224 or :9880) → OpenSearch (:9200)

**Metrics**:  
Services → Backend API (:8080/api/metrics) → PostgreSQL (:5432)

**Traces**:  
Services → Backend API (:8080/api/traces/ingest) → PostgreSQL (:5432)

---

## 📦 Services Overview (Legacy)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **Frontend** | nginx:alpine | 8080 | React dashboard UI |
| **Backend** | api-monitoring-backend:latest | 8081 | Spring Boot REST API |
| **OpenSearch** | opensearchproject/opensearch:latest | 9200 | Log storage & search |
| **Dashboards** | opensearchproject/opensearch-dashboards:latest | 5601 | OpenSearch UI |
| **Fluentd** | (custom build) | 24224, 9880 | Log aggregation |
| **PostgreSQL** | postgres:16 | 5432 | Metrics database |

---

## 🛠️ docker-compose.yml Overview

### Service Configuration

```yaml
version: '3.8'

services:
  opensearch:
    image: opensearchproject/opensearch:latest    # OpenSearch 2.x
    ports:
      - "9200:9200"
    environment:
      OPENSEARCH_INITIAL_ADMIN_PASSWORD: Str0ng@ApiMon#2025
      OPENSEARCH_JAVA_OPTS: "-Xms512m -Xmx512m"

  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:latest
    ports:
      - "5601:5601"
    depends_on:
      opensearch:
        condition: service_healthy

  postgres:
    image: postgres:16                             # PostgreSQL 16.x
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: api_monitoring
      POSTGRES_USER: api_monitor
      POSTGRES_PASSWORD: api_monitor_pass

  fluentd:
    build: ./fluentd
    ports:
      - "24224:24224"
      - "24224:24224/udp"
      - "9880:9880"
    depends_on:
      - opensearch
      - postgres

  backend:
    build: ../../backend/java-apis              # Gradle 9.0.0 + Java 21
    ports:
      - "8081:8081"
    environment:
      SERVER_PORT: 8081
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/api_monitoring
      OPENSEARCH_HOST: opensearch
      OPENSEARCH_PORT: 9200
    depends_on:
      - postgres
      - opensearch
```

---

## 🔧 Common Operations

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f fluentd
docker compose logs -f opensearch
```

### Stop Stack

```bash
# Stop all services
docker compose stop

# Stop specific service
docker compose stop backend

# Remove all containers (keeps volumes)
docker compose down

# Remove everything including volumes
docker compose down -v
```

### Restart Services

```bash
# Restart single service
docker compose restart backend

# Restart all services
docker compose down
docker compose up -d
```

### Database Operations

```bash
# Access PostgreSQL shell
docker compose exec postgres psql -U api_monitor -d api_monitoring

# List databases
\l

# List tables
\dt

# Exit psql
\q
```

### Check Service Health

```bash
# OpenSearch health
docker compose exec opensearch curl -s -k -u admin:Str0ng@ApiMon#2025 https://localhost:9200/_cluster/health | jq .

# PostgreSQL health
docker compose exec postgres pg_isready -U api_monitor

# Backend health
curl http://localhost:8081/health | jq .
```

---

## 📊 Environment Variables

### Backend Configuration

```env
# Server
SERVER_PORT=8081
SPRING_PROFILES_ACTIVE=docker

# Database
SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/api_monitoring
SPRING_DATASOURCE_USERNAME=api_monitor
SPRING_DATASOURCE_PASSWORD=api_monitor_pass

# OpenSearch
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200
OPENSEARCH_SCHEME=https
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=Str0ng@ApiMon#2025
```

### PostgreSQL Configuration

```env
POSTGRES_DB=api_monitoring
POSTGRES_USER=api_monitor
POSTGRES_PASSWORD=api_monitor_pass
```

### OpenSearch Configuration

```env
OPENSEARCH_INITIAL_ADMIN_PASSWORD=Str0ng@ApiMon#2025
OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
```

---

## 📂 Directory Structure

```
infrastructure/
├── docker/
│   ├── docker-compose.yml                    # Main composition file
│   ├── init-scripts/
│   │   └── 01-init-schema.sql               # PostgreSQL initialization
│   ├── fluentd/
│   │   ├── Dockerfile
│   │   ├── conf/
│   │   │   └── fluentd.conf                 # Fluentd configuration
│   │   ├── logs/
│   │   └── README.md
│   └── README.md                            # This file
└── README.md
```

---

## 🔐 Security Configuration

### Default Credentials

> ⚠️ **Change these in production!**

| Service | Username | Password |
|---------|----------|----------|
| OpenSearch | admin | Str0ng@ApiMon#2025 |
| PostgreSQL | api_monitor | api_monitor_pass |

### Update Credentials

```bash
# 1. Change in docker-compose.yml
# 2. Rebuild services
docker compose down
docker compose up -d

# 3. Update application.yaml in backend
# 4. Redeploy backend
```

---

## 🚨 Troubleshooting

### Service Fails to Start

```bash
# Check logs
docker compose logs backend

# Check if port is already in use
lsof -i :8081

# Verify Docker daemon is running
docker ps

# Restart Docker daemon
sudo systemctl restart docker
```

### PostgreSQL Connection Fails

```bash
# Verify PostgreSQL is healthy
docker compose ps postgres

# Check logs
docker compose logs postgres

# Test connection
docker compose exec postgres psql -U api_monitor -d api_monitoring -c "SELECT 1"
```

### OpenSearch Connection Issues

```bash
# Check OpenSearch health
curl -k -u admin:Str0ng@ApiMon#2025 https://localhost:9200

# Check logs
docker compose logs opensearch

# Verify network
docker network ls
docker network inspect docker_monitoring-net
```

### Out of Disk Space

```bash
# Remove unused volumes
docker volume prune

# Remove old images
docker image prune -a

# Clean up everything (careful!)
docker system prune -a -v
```

### Memory/CPU Issues

```bash
# Check resource usage
docker stats

# Increase Docker memory limit
# Edit Docker Desktop preferences or daemon.json

# Reduce OpenSearch heap
# In docker-compose.yml: OPENSEARCH_JAVA_OPTS: "-Xms256m -Xmx256m"
```

---

## 📊 Performance Tuning

### For Development

```yaml
# docker-compose.yml - Reduced resources
opensearch:
  environment:
    OPENSEARCH_JAVA_OPTS: "-Xms256m -Xmx256m"
```

### For Production

```yaml
# Increase resources
opensearch:
  environment:
    OPENSEARCH_JAVA_OPTS: "-Xms2g -Xmx2g"
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 3G
```

---

## 🔄 Backup & Restore

### Backup Data

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U api_monitor api_monitoring > backup.sql

# Backup OpenSearch indices
curl -k -u admin:Str0ng@ApiMon#2025 https://localhost:9200/_snapshot/backup
```

### Restore Data

```bash
# Restore PostgreSQL
docker compose exec -T postgres psql -U api_monitor api_monitoring < backup.sql

# Restore OpenSearch from snapshot
curl -k -u admin:Str0ng@ApiMon#2025 -X POST https://localhost:9200/_snapshot/backup/restore
```

---

## 📚 Component Versions

| Component | Version | Notes |
|-----------|---------|-------|
| PostgreSQL | 16.x | Latest stable |
| OpenSearch | 2.x | Latest stable |
| OpenSearch Dashboards | 2.x | Matches OpenSearch |
| Fluentd | 1.16.x | Log aggregation |
| Java (Backend) | 21 LTS | OpenJDK |
| Gradle (Build) | 9.0.0+ | Backend build |
| Node.js (Frontend) | 20.x LTS | Frontend build |
| Nginx (Frontend Runtime) | Alpine | Lightweight |
| Docker | 29.x+ | 29.1.3+ |
| Docker Compose | 2.39.x+ | 2.39.1+ |

---

## 🔗 Access Points

### Dashboard & UIs

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:8080 | N/A |
| Backend API | http://localhost:8081 | N/A |
| Backend Actuator | http://localhost:8081/actuator | N/A |
| OpenSearch Dashboards | http://localhost:5601 | admin / Str0ng@ApiMon#2025 |
| OpenSearch API | https://localhost:9200 | admin / Str0ng@ApiMon#2025 |
| PostgreSQL | localhost:5432 | api_monitor / api_monitor_pass |
| Fluentd | http://localhost:9880 | N/A |

---

## 📝 License

[Your License Here]
