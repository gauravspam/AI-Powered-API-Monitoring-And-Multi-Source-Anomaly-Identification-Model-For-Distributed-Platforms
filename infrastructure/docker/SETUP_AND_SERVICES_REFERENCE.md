# Infrastructure & Docker - Setup & Services Reference Guide

## Overview

This folder contains Docker Compose configuration and infrastructure services for the API Monitoring Platform. It includes PostgreSQL for data storage, OpenSearch for log aggregation, and Fluentd for log forwarding.

**Default Ports:**
- PostgreSQL: 5433 → 5432
- OpenSearch: 9200, 9600
- Fluentd: 24224 (TCP/UDP), 9880 (HTTP), 24231 (Prometheus), 8888 (Health)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Services](#services)
3. [Configuration](#configuration)
4. [Starting Services](#starting-services)
5. [Stopping Services](#stopping-services)
6. [Data Persistence](#data-persistence)
7. [Health Checks](#health-checks)
8. [Network Configuration](#network-configuration)
9. [Log Forwarding](#log-forwarding)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Start All Services

```powershell
cd infrastructure/docker
docker-compose up -d
```

### Check Status

```powershell
docker-compose ps
```

### View Logs

```powershell
docker-compose logs -f
```

---

## Services

### 1. PostgreSQL

**Container:** `postgres`
**Image:** `postgres:16`
**Port:** `5433:5432` (mapped to localhost:5433)

**Environment Variables:**
| Variable | Value |
|----------|-------|
| POSTGRES_DB | api_monitoring |
| POSTGRES_USER | api_monitor |
| POSTGRES_PASSWORD | api_monitor_pwd |

**Purpose:** Primary database for storing:
- Metrics
- Traces
- Anomalies
- Alerts

**Storage:** Docker volume `postgres_data`

**Health Check:**
```bash
pg_isready -U api_monitor -d api_monitoring
```

---

### 2. OpenSearch

**Container:** `opensearch`
**Image:** `opensearchproject/opensearch:2.17.0`
**Ports:**
- 9200:9200 (REST API)
- 9600:9600 (Performance Analyzer)

**Environment Variables:**
| Variable | Value |
|----------|-------|
| cluster.name | docker-cluster |
| node.name | opensearch-node1 |
| OPENSEARCH_JAVA_OPTS | -Xms512m -Xmx512m |
| OPENSEARCH_INITIAL_ADMIN_PASSWORD | Admin123! |
| DISABLE_SECURITY_PLUGIN | true |

**Purpose:** Log storage and search engine

**Storage:** Docker volume `opensearch_data`

**Health Check:**
```bash
curl -s http://localhost:9200 >/dev/null
```

**Usage:**
- Access OpenSearch Dashboards: http://localhost:9200
- Username: admin
- Password: Admin123!

---

### 3. Fluentd

**Container:** `fluentd`
**Build:** `./fluentd/Dockerfile`
**Ports:**
- 24224:24224 (TCP Forward)
- 24224:24224/udp (UDP Forward)
- 9880:9880 (HTTP Input)
- 24231:24231 (Prometheus)
- 8888:8888 (Health)

**Purpose:** Log collection and forwarding to OpenSearch

**Config File:** `fluent.conf`

**Storage:** Docker volume `fluentd_buffer`

**Health Check:**
```bash
wget --spider -q http://127.0.0.1:8888/api/plugins.json
```

---

## Configuration Files

### docker-compose.yml

The main orchestration file defining all services.

**Key Sections:**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: api_monitoring
      POSTGRES_USER: api_monitor
      POSTGRES_PASSWORD: api_monitor_pwd
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U api_monitor -d api_monitoring"]
    restart: unless-stopped

  opensearch:
    image: opensearchproject/opensearch:2.17.0
    environment:
      - bootstrap.memory_lock=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
      - DISABLE_SECURITY_PLUGIN=true
    ulimits:
      memlock:
        soft: -1
        hard: -1

  fluentd:
    build:
      context: ./fluentd
      dockerfile: Dockerfile
    volumes:
      - ./fluent.conf:/fluentd/etc/fluent.conf:ro

networks:
  monitoring-net:

volumes:
  postgres_data:
  opensearch_data:
  fluentd_buffer:
```

---

### fluent.conf

Fluentd configuration for log collection and forwarding.

**Input Sources:**

| Source | Port | Protocol | Purpose |
|--------|------|----------|---------|
| forward | 24224 | TCP | Fluentd forward protocol |
| http | 9880 | HTTP | Direct POST from apps |
| monitor_agent | 8888 | HTTP | Health check |
| prometheus | 24231 | HTTP | Fluentd metrics |

**Output:**

- **Primary:** OpenSearch (opensearch:9200)
- **Secondary:** stdout (fallback)

**Index Configuration:**
- Index prefix: `logs`
- Daily indices: `logs-2026.04.11`
- Logstash format: enabled

**Buffer Settings:**
- Flush interval: 10 seconds
- Buffer size: 512MB max
- Retry: exponential backoff

---

## Starting Services

### Start All Services

```powershell
cd infrastructure/docker
docker-compose up -d
```

### Start Specific Service

```powershell
docker-compose up -d postgres
docker-compose up -d opensearch
docker-compose up -d fluentd
```

### Start with Logs

```powershell
docker-compose up
```

### Rebuild and Start

```powershell
docker-compose up --build -d
```

---

## Stopping Services

### Stop All Services

```powershell
docker-compose down
```

### Stop and Remove Volumes

```powershell
docker-compose down -v
```

### Stop and Remove Images

```powershell
docker-compose down --rmi all
```

### Stop and Remove Everything

```powershell
docker-compose down -v --rmi all
```

---

## Data Persistence

### Docker Volumes

| Volume | Service | Purpose |
|--------|---------|---------|
| postgres_data | postgres | Database data |
| opensearch_data | opensearch | Log indices |
| fluentd_buffer | fluentd | Buffer files |

### View Volumes

```powershell
docker volume ls
```

### Inspect Volume

```powershell
docker volume inspect infrastructure-docker_postgres_data
```

### Remove Unused Volumes

```powershell
docker volume prune
```

---

## Health Checks

### Check All Services

```powershell
docker-compose ps
```

All services have health checks configured:
- PostgreSQL: `pg_isready`
- OpenSearch: `curl localhost:9200`
- Fluentd: `wget localhost:8888`

### Check Specific Service Health

```powershell
docker inspect --format='{{.State.Health.Status}}' postgres
docker inspect --format='{{.State.Health.Status}}' opensearch
docker inspect --format='{{.State.Health.Status}}' fluentd
```

### Wait for Healthy Services

```powershell
docker-compose up -d
docker-compose ps --format json | jq '.'
docker-compose wait postgres opensearch
```

---

## Network Configuration

### Network Name

`monitoring-net`

All services are on the same Docker network for inter-service communication.

### Service Communication

| From | To | Address |
|------|------|---------|
| Backend | PostgreSQL | `postgres:5432` |
| Fluentd | OpenSearch | `opensearch:9200` |
| Frontend | Backend | `backend:8080` |

### Access from Host

| Service | Host Port | URL |
|---------|----------|-----|
| PostgreSQL | 5433 | localhost:5433 |
| OpenSearch | 9200 | http://localhost:9200 |
| Fluentd (HTTP) | 9880 | http://localhost:9880 |
| Fluentd (Forward) | 24224 | fluentd://24224 |

---

## Log Forwarding

### Send Logs via HTTP

```bash
# Send a log to Fluentd
curl -X POST http://localhost:9880/app.logs \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-04-11T10:30:00Z",
    "level": "INFO",
    "serviceName": "user-service",
    "message": "User login successful"
  }'
```

### Send Logs via Fluentd Forward

```bash
# Using fluent-logger (example)
<source>
  @type forward
  port 24224
</source>
```

### View Fluentd Logs

```powershell
docker-compose logs fluentd
```

### Check Fluentd Buffer

```bash
docker exec fluentd ls -la /fluentd/log/
```

---

## Troubleshooting

### Issue: PostgreSQL Connection Refused

**Error:**
```
psql: could not connect to server
```

**Solution:**
```powershell
# Check container status
docker ps | findstr postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Recreate container
docker-compose up -d postgres
```

---

### Issue: OpenSearch Not Responding

**Error:**
```
curl: (7) Failed to connect
```

**Solution:**
```powershell
# Check OpenSearch logs
docker-compose logs opensearch

# Check memory limits (may need to increase)
# OpenSearch requires at least 512MB and locked memory

# Restart with more memory
docker-compose up -d opensearch
```

---

### Issue: Fluentd Not Forwarding Logs

**Error:**
Logs not appearing in OpenSearch

**Solution:**
```powershell
# Check Fluentd logs
docker-compose logs fluentd

# Check buffer
docker exec fluentd ls /fluentd/log/

# Check OpenSearch connection
docker exec fluentd wget -qO- http://opensearch:9200

# Restart Fluentd
docker-compose restart fluentd
```

---

### Issue: Port Already in Use

**Error:**
```
Bind for 0.0.0.0:5433 failed: port is already allocated
```

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr 5433

# Stop conflicting service or change port in docker-compose.yml
```

---

### Issue: Out of Disk Space

**Error:**
```
No space left on device
```

**Solution:**
```powershell
# Clean up Docker
docker system prune -a

# Prune volumes
docker volume prune

# Prune build cache
docker builder prune
```

---

### Issue: Services Won't Start

**Error:**
```
level=error msg="failed to start"
```

**Solution:**
```powershell
# Check for port conflicts
docker-compose ps

# Check for volume conflicts
docker volume ls

# Clean start
docker-compose down
docker-compose up -d
```

---

## Common Commands

### View All Containers

```powershell
docker ps -a
```

### View Logs

```powershell
docker-compose logs -f postgres
docker-compose logs -f opensearch
docker-compose logs -f fluentd
```

### Execute Command in Container

```powershell
# PostgreSQL
docker exec -it postgres psql -U api_monitor -d api_monitoring

# OpenSearch
docker exec -it opensearch ls /usr/share/opensearch/data

# Fluentd
docker exec -it fluentd ls /fluentd/log/
```

### Backup PostgreSQL

```powershell
docker exec postgres pg_dump -U api_monitor api_monitoring > backup.sql
```

### Restore PostgreSQL

```powershell
docker exec -i postgres psql -U api_monitor api_monitoring < backup.sql
```

---

## Environment Variables Reference

### PostgreSQL

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_DB | Database name | api_monitoring |
| POSTGRES_USER | Database user | api_monitor |
| POSTGRES_PASSWORD | Database password | api_monitor_pwd |

### OpenSearch

| Variable | Description | Default |
|----------|-------------|---------|
| cluster.name | Cluster name | docker-cluster |
| node.name | Node name | opensearch-node1 |
| OPENSEARCH_JAVA_OPTS | JVM options | -Xms512m -Xmx512m |
| OPENSEARCH_INITIAL_ADMIN_PASSWORD | Admin password | Admin123! |
| DISABLE_SECURITY_PLUGIN | Disable security | true |

### Fluentd

| Variable | Description | Default |
|----------|-------------|---------|
| FLUENTD_CONF | Config file | fluent.conf |
| OPENSEARCH_HOST | OpenSearch host | opensearch |
| OPENSEARCH_PORT | OpenSearch port | 9200 |

---

## Related Files

| File | Description |
|------|-------------|
| docker-compose.yml | Main orchestration |
| fluent.conf | Fluentd configuration |
| fluentd/Dockerfile | Fluentd image |
| init-scripts/*.sql | Database initialization |
| backup.sql | Database backup template |

---

## Quick Reference

### Start All

```powershell
docker-compose up -d
```

### Stop All

```powershell
docker-compose down
```

### Check Status

```powershell
docker-compose ps
```

### View Logs

```powershell
docker-compose logs -f
```

### Connect to PostgreSQL

```powershell
docker exec -it postgres psql -U api_monitor -d api_monitoring
```

### Test OpenSearch

```powershell
curl http://localhost:9200
```

### Test Fluentd

```powershell
curl http://localhost:9880
```