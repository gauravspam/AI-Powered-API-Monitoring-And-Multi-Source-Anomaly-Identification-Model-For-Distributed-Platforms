# AI-Powered API Monitoring and Multi-Source Anomaly Identification Model

A distributed platform for monitoring APIs, collecting logs from multiple sources, and identifying anomalies using AI/ML models (MSFI-LSTM and PLE-GRU).

## 🏗️ Architecture Overview

This platform implements a comprehensive monitoring solution with the following components:

1. **Sources** - Application logs (SLF4J/Log4j2), SaaS/cloud-native services, and event/log sources
2. **Secret Injection** - Vault-based component for secure credential management
3. **Collector Agent Layer** - Fluent Bit and OpenTelemetry Collector agents for log collection
4. **Central Log Aggregation** - Fluentd router/aggregator for log forwarding
5. **Log & Metric Storage** - OpenSearch (logs/metrics) and PostgreSQL (metadata/config)
6. **ML Anomaly Detection** - MSFI-LSTM and PLE-GRU models for anomaly identification
7. **Visualization** - OpenSearch Dashboards and custom React frontend
8. **Alerting** - Slack, PagerDuty, and email notifications

See `docs/PROJECT_OVERVIEW.md` for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Java 25+ (for backend)
- Node.js 18+ and npm (for frontend)
- Python 3.9+ (for ML models)

### Running the Platform

1. **Start Infrastructure Services:**
   ```bash
   cd infrastructure/docker
   docker compose up -d
   ```

   This starts:
   - OpenSearch (port 9200)
   - OpenSearch Dashboards (port 5601)
   - PostgreSQL (port 5432)
   - Fluentd (port 24224)

2. **Start Backend:**
   ```bash
   cd backend/java-apis
   ./gradlew bootRun
   ```
   Backend runs on `http://localhost:8080`

3. **Start Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend runs on `http://localhost:5173` (Vite default)

### Verify Installation

- Backend Health: `curl http://localhost:8080/health`
- OpenSearch: `curl -k https://localhost:9200 -u admin:Str0ng@ApiMon#2025`
- OpenSearch Dashboards: `http://localhost:5601`
- PostgreSQL: `psql -h localhost -U api_monitor -d api_monitoring`

## 📁 Project Structure

```
├── backend/              # Spring Boot backend API
│   └── java-apis/       # Main backend application
├── frontend/            # React frontend application
├── ml-models/           # ML model implementations (MSFI-LSTM, PLE-GRU)
├── infrastructure/       # Infrastructure as code
│   └── docker/          # Docker Compose configurations
│   └── fluent-bit/      # Fluent Bit agent configurations
│   └── fluentd/         # Fluentd aggregator configurations
└── docs/                # Documentation
    ├── api-contracts.md # API endpoint documentation
    └── PROJECT_OVERVIEW.md # Architecture details
```

## 🛠️ Tech Stack

- **Backend:** Spring Boot, Java 25, OpenSearch Client, PostgreSQL
- **Frontend:** React 19, Material-UI, Vite, Axios
- **ML Models:** Python (TensorFlow/PyTorch), MSFI-LSTM, PLE-GRU
- **Infrastructure:** Docker, Docker Compose, Fluentd, Fluent Bit
- **Storage:** OpenSearch, PostgreSQL
- **Monitoring:** OpenSearch Dashboards

## 👥 Team & Responsibilities

- **Gaurav** - Backend (Java/Spring Boot), Docker/Infrastructure, OpenSearch Integration
- **Sujal** - Frontend (React), PostgreSQL Schema & Migrations, UI/UX

## 📚 Documentation

- [API Contracts](docs/api-contracts.md) - Backend API documentation
- [Project Overview](docs/PROJECT_OVERVIEW.md) - Detailed architecture
- [Contributing Guide](CONTRIBUTING.md) - Development workflow and guidelines
- [Backend README](backend/README.md) - Backend setup and development
- [Frontend README](frontend/README.md) - Frontend setup and development
- [Infrastructure README](infrastructure/README.md) - Deployment guide

## 🔧 Configuration

### Environment Variables

Copy environment variable templates and configure:

- Backend: `backend/.env.example` → `backend/.env`
- Frontend: `frontend/.env.example` → `frontend/.env`

See environment variable templates for required configuration.

## 🧪 Development

### Running Tests

**Backend:**
```bash
cd backend/java-apis
./gradlew test
```

**Frontend:**
```bash
cd frontend
npm test
```

### Code Quality

- Backend: Follow Java coding standards, use Spring Boot best practices
- Frontend: ESLint configured, follow React best practices

## 📊 Features

- ✅ Centralized log aggregation from multiple sources
- ✅ Real-time log search and analysis via OpenSearch
- ✅ ML-powered anomaly detection
- ✅ Customizable alert rules
- ✅ Multi-channel notifications (Slack, PagerDuty, Email)
- ✅ Interactive dashboards and visualizations
- ✅ API monitoring and health tracking

## 🔐 Security Notes

- Default passwords in `docker-compose.yml` are for development only
- Use environment variables for production secrets
- Implement Vault integration for production deployments
- Enable SSL/TLS for all services in production

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## 📝 License

[Add your license here]

## 🔗 Links

- **GitHub Repository:** [https://github.com/gauravspam/AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms](https://github.com/gauravspam/AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms)
- **OpenSearch Documentation:** https://opensearch.org/docs/
- **Fluentd Documentation:** https://docs.fluentd.org/
