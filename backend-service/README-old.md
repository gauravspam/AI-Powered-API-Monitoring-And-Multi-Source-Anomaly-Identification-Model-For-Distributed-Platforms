# 🔧 Backend - Spring Boot API

Spring Boot 3.2.1 REST API for API monitoring, metrics collection, and anomaly detection.

---

## 📋 Prerequisites

- **Java 21** (OpenJDK LTS) - `openjdk 21.0.9` or higher
- **Gradle 9.0.0** or higher
- **PostgreSQL 16.x** (for development) or Docker for containerized deployment
- **OpenSearch 2.x** (for log storage) or Docker for containerized deployment

---

## 🏗️ Project Structure

```
backend/java-apis/
├── src/
│   ├── main/
│   │   ├── java/com/api/monitoring/backend/
│   │   │   ├── ApiMonitoringBackendApplication.java    # Spring Boot entry point
│   │   │   ├── controller/
│   │   │   ├── service/
│   │   │   ├── repository/
│   │   │   ├── model/
│   │   │   ├── config/
│   │   │   └── exception/
│   │   └── resources/
│   │       ├── application.yaml                        # Default config
│   │       ├── application-docker.yaml                # Docker environment config
│   │       └── application.properties
│   └── test/
│       └── java/com/api/monitoring/backend/
├── build.gradle                                         # Gradle build config (Java 21, Spring 3.2.1)
├── gradle/wrapper/gradle-wrapper.properties            # Gradle 9.0.0 wrapper
├── Dockerfile                                           # Multi-stage build (Java 21)
└── README.md                                            # This file
```

---

## 🔨 Build & Development

### Local Development

```bash
# Install dependencies and build
gradle build -x test

# Run tests
gradle test

# Run the application (development mode)
gradle bootRun
```

The backend will start on `http://localhost:8080` (default port)

### Docker Build

```bash
# Build Docker image
docker build -t api-monitoring-backend .

# Run with Docker (requires PostgreSQL & OpenSearch running)
docker run -d \
  -p 8081:8081 \
  -e SERVER_PORT=8081 \
  -e SPRING_DATASOURCE_URL=jdbc:postgresql://host.docker.internal:5432/api_monitoring \
  -e SPRING_DATASOURCE_USERNAME=api_monitor \
  -e SPRING_DATASOURCE_PASSWORD=api_monitor_pass \
  -e OPENSEARCH_HOST=host.docker.internal \
  -e OPENSEARCH_PORT=9200 \
  api-monitoring-backend
```

---

## 📦 Key Dependencies

### Spring Boot Stack
- **Spring Boot 3.2.1** - REST API framework
- **Spring Data JPA** - Database ORM
- **Spring Boot Actuator** - Health checks & metrics

### Database & Search
- **PostgreSQL Driver** - Primary metrics storage
- **OpenSearch REST Client 2.13.0** - Log search & analytics

### JSON & Serialization
- **Jackson Databind 2.18.1** - JSON processing
- **H2 Database** - In-memory testing database

---

## 🛠️ Configuration

### Application Profiles

The application uses Spring profiles to manage environments:

- **default** (`application.yaml`) - Development with H2 in-memory DB
- **docker** (`application-docker.yaml`) - Production with PostgreSQL & OpenSearch

### Environment Variables (Docker)

```bash
SERVER_PORT=8081                                          # Server port (default: 8080)
SPRING_PROFILES_ACTIVE=docker                            # Use docker profile
SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/api_monitoring
SPRING_DATASOURCE_USERNAME=api_monitor
SPRING_DATASOURCE_PASSWORD=api_monitor_pass
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200
OPENSEARCH_SCHEME=https
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=Str0ng@ApiMon#2025
```

---

## 🚀 Deployment

### Docker Compose (Recommended)

```bash
cd infrastructure/docker
docker compose up -d
```

This starts:
- **PostgreSQL 16** on port 5432
- **OpenSearch 2.x** on port 9200
- **Backend** on port 8081
- **OpenSearch Dashboards** on port 5601
- **Fluentd** on port 24224

### Health Check

```bash
# Check backend health
curl http://localhost:8081/health

# Check actuator endpoints
curl http://localhost:8081/actuator
```

---

## 📝 API Endpoints

Base URL: `http://localhost:8081`

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health status |
| `GET` | `/actuator` | Available actuator endpoints |
| `GET` | `/actuator/health` | Detailed health info |

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8081
lsof -i :8081

# Kill process on port 8081
kill -9 <PID>
```

### Gradle Build Fails
```bash
# Clear Gradle cache
gradle clean

# Verify Gradle version
gradle --version  # Should be 9.0.0+

# Rebuild with debug
gradle build --debug
```

### Docker Build Issues
```bash
# Check Docker logs
docker logs api-monitoring-backend

# Rebuild without cache
docker build --no-cache -t api-monitoring-backend .
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U api_monitor -d api_monitoring

# Test OpenSearch connection
curl -k -u admin:Str0ng@ApiMon#2025 https://localhost:9200
```

---

## 📊 Metrics & Monitoring

- **Spring Boot Actuator** - Application metrics at `/actuator/metrics`
- **OpenSearch** - Log aggregation and analysis
- **PostgreSQL** - Structured metrics storage

---

## 🔄 CI/CD

Uses multi-stage Docker build for optimized image size:
1. **Build stage** - Compiles with Gradle 9.0.0
2. **Runtime stage** - Runs with Java 21 JRE

---

## 📚 Additional Resources

- [Spring Boot 3.2.1 Docs](https://spring.io/projects/spring-boot)
- [Gradle 9.0.0 Docs](https://docs.gradle.org/9.0.0/)
- [OpenSearch Documentation](https://opensearch.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## ⚙️ Version Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Java | 21 LTS | OpenJDK 21.0.9+ |
| Gradle | 9.0.0+ | Latest stable |
| Spring Boot | 3.2.1 | Latest stable 3.x |
| PostgreSQL | 16.x | Latest stable |
| OpenSearch | 2.x | Latest stable |
| Docker | 29.x+ | 29.1.3+ |

---

## 📝 License

[Your License Here]
