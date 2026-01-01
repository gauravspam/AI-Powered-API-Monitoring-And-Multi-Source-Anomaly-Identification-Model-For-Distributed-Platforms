# 🚀 AI-Powered API Monitoring & Multi-Source Anomaly Identification

**Real-time API anomaly detection** using **Machine Learning** with distributed monitoring, log aggregation, and intelligent alerting.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Linux Installation Guide](#linux-installation-guide)
5. [Quick Start](#quick-start)
6. [Running the Application](#running-the-application)
7. [Verification & Testing](#verification--testing)
8. [API Documentation](#api-documentation)
9. [Troubleshooting](#troubleshooting)
10. [Project Roadmap](#project-roadmap)

---

## 📊 Overview

### What It Does

- **API Monitoring**: Real-time metrics collection (CPU, Memory, Response Time, Error Rate)
- **Anomaly Detection**: ML-powered detection using Isolation Forest + LSTM
- **Log Aggregation**: Centralized logging with Fluentd → OpenSearch
- **Alert Management**: Intelligent alerts with custom thresholds
- **Multi-Source Analysis**: Correlates metrics, logs, and traces for root cause analysis

### Key Features

✅ **Spring Boot 3.2** REST API with PostgreSQL  
✅ **Real-time Metrics** collection and aggregation  
✅ **ML Models**: Isolation Forest (Stage 1), LSTM (Stage 2)  
✅ **OpenSearch** for log search & analytics  
✅ **Docker Compose** for easy deployment  
✅ **Fluentd** for log forwarding  
✅ **Zero Production Dependencies**: No Redis, Kafka, or Prometheus  

---

## 🏗️ Architecture


![alt text](/src/images/sys_arch.jpg)

---

## ✅ Prerequisites

### Required Software 

- Java 21 (OpenJDK)
- Gradle 8.5
- Docker 25.x
- Docker Compose 2.24+
- Git
- PostgreSQL Client (psql)

---

## 🔧 Linux Installation Guide

### Copy-paste each section into terminal in order.

#### **Phase 1: System Update**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git htop neofetch build-essential postgresql-client unzip apt-transport-https ca-certificates gnupg lsb-release
```

#### **Phase 2: Java 21 Installation**

```bash
sudo apt install -y openjdk-21-jdk openjdk-21-jre
java --version  # Verify: openjdk 21.0.x
```

#### **Phase 3: Gradle 8.5 Installation**

```bash
# Download Gradle 8.5
wget https://services.gradle.org/distributions/gradle-8.5-bin.zip

# Install system-wide
sudo rm -rf /opt/gradle* 2>/dev/null || true
sudo unzip -o gradle-8.5-bin.zip -d /opt/
sudo ln -sf /opt/gradle-8.5 /opt/gradle

# Add to PATH
echo 'export PATH=/opt/gradle/bin:$PATH' >> ~/.bashrc
echo 'export GRADLE_USER_HOME=$HOME/.gradle' >> ~/.bashrc
source ~/.bashrc

# Verify
gradle --version  # Should show: Gradle 8.5
```

#### **Phase 4: Docker & Docker Compose**

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose 2.24.0
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version      # Docker version 25.x
docker-compose --version  # Docker Compose 2.24.0
```

#### **Phase 5: Clone Repository**

```bash
# Clone the repo
git clone https://github.com/gauravspam/AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms.git

cd AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms

# Fix Gradle lock files for clean Git history
cat >> .gitignore << 'EOF'

# Gradle cache (NEVER commit)
.gradle/
build/
*.lock
backend/java-apis/.gradle/
backend/java-apis/build/
!backend/java-apis/gradlew
!backend/java-apis/gradlew.bat
EOF

# Clean cached files
find backend -name "*.lock" -delete 2>/dev/null || true
git rm -r --cached backend/java-apis/.gradle/ 2>/dev/null || true
git add .gitignore
git commit -am "build: Add Gradle cache to gitignore [skip ci]" 2>/dev/null || true
```

#### **Phase 6: Docker Compose Stack (PostgreSQL + OpenSearch + Fluentd)**

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL: Metrics storage
  postgres:
    image: postgres:15.6
    container_name: postgres-anomaly
    environment:
      POSTGRES_DB: anomaly_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # OpenSearch: Log storage & search
  opensearch:
    image: opensearchproject/opensearch:2.7.0
    container_name: opensearch-anomaly
    environment:
      - discovery.type=single-node
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=AnomalyMonitor@2026
      - plugins.security.disabled=true
    ports:
      - "9200:9200"
      - "9600:9600"
    volumes:
      - opensearch_data:/usr/share/opensearch/data

volumes:
  postgres_data:
  opensearch_data:
EOF

# Start services
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start (30s)..."
sleep 30

# Verify
docker-compose ps  # Should show 2 services: postgres (healthy), opensearch (healthy)
```

#### **Phase 7: Fluentd Installation**

```bash
# Install Fluentd
curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-jammy-fluentd.sh | sh

# Start Fluentd
sudo systemctl enable td-agent
sudo systemctl start td-agent

# Verify
td-agent --version  # Should show: 1.16.x
```

---

## 🚀 Quick Start

### 1. Build Backend Application

```bash
cd backend/java-apis

# Clean build
./gradlew clean build

# Or skip tests for faster build
./gradlew clean build -x test
```

### 2. Configure Application

```bash
# Edit application.yml with database credentials
cat > src/main/resources/application.yml << 'EOF'
server:
  port: 8080

spring:
  application:
    name: anomaly-api
  datasource:
    url: jdbc:postgresql://localhost:5432/anomaly_db
    username: postgres
    password: password
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: always

logging:
  level:
    com.api.monitoring: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
EOF
```

### 3. Run Backend

```bash
# Start Spring Boot application
./gradlew bootRun
```

**Expected Output**:
```
Started AnomalyApplication in 5.234 seconds
Tomcat started on port(s): 8080 (http)
```

---

## 🔄 Running the Application

### Terminal 1: Docker Stack (Background)

```bash
# Start PostgreSQL + OpenSearch + Fluentd
docker-compose up -d

# Monitor logs
docker-compose logs -f
```

### Terminal 2: Backend API

```bash
cd backend/java-apis
./gradlew bootRun
```

### Terminal 3: Test APIs (While backend runs)

```bash
# Check backend health
curl http://localhost:8080/actuator/health

# Ingest metrics
curl -X POST http://localhost:8080/api/v1/metrics/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "cpuUsage": 75.5,
    "memoryUsage": 62.3,
    "responseTimeMs": 2500,
    "errorRate": 0.08,
    "requestCount": 1500,
    "timestamp": "2026-01-01T12:30:00"
  }'

# Get metrics
curl http://localhost:8080/api/v1/metrics

# Run anomaly detection
curl -X POST http://localhost:8080/api/v1/anomalies/detect \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## ✅ Verification & Testing

### 1. Service Health Check

```bash
#!/bin/bash
echo "🔍 Verifying All Services..."

# Java version
echo "✅ Java:"
java --version | head -1

# Gradle version
echo "✅ Gradle:"
gradle --version | head -1

# Docker
echo "✅ Docker Services:"
docker-compose ps

# Backend API
echo "✅ Backend Health:"
curl -s http://localhost:8080/actuator/health | jq .

# PostgreSQL
echo "✅ PostgreSQL:"
psql -h localhost -U postgres -d anomaly_db -c "SELECT version();" 2>/dev/null || echo "⚠️ PostgreSQL not accessible"

# OpenSearch
echo "✅ OpenSearch:"
curl -s -u "admin:admin" http://localhost:9200/_cluster/health 2>/dev/null | jq . || curl -s http://localhost:9200/_cluster/health | jq .

# Fluentd
echo "✅ Fluentd:"
td-agent-ctl status 2>/dev/null || sudo systemctl status td-agent --no-pager | head -3
```

### 2. Database Verification

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d anomaly_db

# Inside psql:
\dt  # List tables

# Check metrics table
SELECT COUNT(*) FROM metric_records;

# Exit
\q
```

### 3. API Testing

```bash
# Ingest sample metrics
for i in {1..10}; do
  curl -X POST http://localhost:8080/api/v1/metrics/ingest \
    -H "Content-Type: application/json" \
    -d "{
      \"cpuUsage\": $((RANDOM % 100)),
      \"memoryUsage\": $((RANDOM % 100)),
      \"responseTimeMs\": $((RANDOM % 5000)),
      \"errorRate\": 0.$(RANDOM % 100),
      \"requestCount\": $((RANDOM % 10000)),
      \"timestamp\": \"$(date -u +'%Y-%m-%dT%H:%M:%S')\"
    }"
  echo "✅ Metric $i ingested"
  sleep 1
done

# Get all metrics
echo "📊 All Metrics:"
curl -s http://localhost:8080/api/v1/metrics | jq .

# Run anomaly detection
echo "🔍 Running Anomaly Detection:"
curl -X POST http://localhost:8080/api/v1/anomalies/detect | jq .
```

### 4. Logs Verification

```bash
# Check application logs
./gradlew bootRun | grep -E "ERROR|WARN|Metric|Anomaly"

# View Docker logs
docker-compose logs postgres
docker-compose logs opensearch

# Fluentd logs
sudo tail -f /var/log/td-agent/td-agent.log
```

---

## 📖 API Documentation

### Base URL: `http://localhost:8080`

#### **1. Health Check**
```bash
GET /actuator/health
Response: { "status": "UP" }
```

#### **2. Ingest Metrics**
```bash
POST /api/v1/metrics/ingest
Content-Type: application/json

{
  "cpuUsage": 75.5,
  "memoryUsage": 62.3,
  "responseTimeMs": 2500,
  "errorRate": 0.08,
  "requestCount": 1500,
  "timestamp": "2026-01-01T12:30:00"
}
```

#### **3. Get All Metrics**
```bash
GET /api/v1/metrics
Response: [{...metric objects...}]
```

#### **4. Detect Anomalies**
```bash
POST /api/v1/anomalies/detect
Response: [{...anomaly records...}]
```

#### **5. Create Alert**
```bash
POST /api/v1/alerts/create
Content-Type: application/json

{
  "alertName": "High CPU Alert",
  "threshold": 85.0,
  "enabled": true,
  "notificationChannels": ["email", "slack"]
}
```

#### **6. Get Alerts**
```bash
GET /api/v1/alerts
Response: [{...alert records...}]
```

---

## 🐛 Troubleshooting

### Issue: PostgreSQL Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres

# Test connection
psql -h localhost -U postgres -d anomaly_db -c "SELECT 1;"
```

### Issue: OpenSearch Not Starting

```bash
# Check logs
docker-compose logs opensearch

# Restart
docker-compose restart opensearch

# Verify
curl -u "admin:admin" http://localhost:9200
```

### Issue: Gradle Lock Issues

```bash
# Clean Gradle cache completely
./gradlew clean --stop
rm -rf ~/.gradle/
rm -rf backend/java-apis/.gradle/
rm -rf backend/java-apis/build/

# Rebuild
./gradlew clean build
```

### Issue: Port Already in Use

```bash
# Find process using port 8080
lsof -i :8080
# Kill it
kill -9 <PID>

# Or use different port in application.yml:
server:
  port: 8081
```

### Issue: Docker Permissions

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group immediately
newgrp docker

# Or use sudo
sudo docker-compose up -d
```

---

<div align="center">
  
**Built with ❤️ for the DevOps and SRE community** <br>
**Last Updated**: January 1, 2026  
⭐ If you find this project helpful, please star it on GitHub!

</div>
