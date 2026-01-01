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
