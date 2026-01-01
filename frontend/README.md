# 🎨 Frontend - React Dashboard

React 18+ web application for API monitoring, anomaly detection visualization, and alert management.

---

## 📋 Prerequisites

- **Node.js 20.x LTS** - `20.x.x` or higher
- **npm 10.x** - Included with Node.js 20.x
- **Docker 29.x** (optional) - For containerized deployment

---

## 📚 Project Structure

```
frontend/
├── src/
│   ├── main.jsx                          # React entry point
│   ├── App.jsx                           # Root component
│   ├── index.css                         # Global styles
│   ├── theme.js                          # Theme configuration
│   ├── components/                       # Reusable components
│   │   ├── AlertList.jsx
│   │   ├── AnomalyTable.jsx
│   │   ├── EnvironmentFilter.jsx
│   │   ├── LogTimeline.jsx
│   │   ├── MetricChart.jsx
│   │   ├── SideNav.jsx
│   │   ├── StatCard.jsx
│   │   ├── StatusChip.jsx
│   │   └── TopBar.jsx
│   ├── pages/                            # Page components
│   │   ├── Alerts.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Logs.jsx
│   │   ├── Models.jsx
│   │   ├── Services.jsx
│   │   ├── Settings.jsx
│   │   └── NotFound.jsx
│   ├── layouts/                          # Layout components
│   │   └── MainLayout.jsx
│   ├── routes/                           # Route definitions
│   │   └── AppRoutes.jsx
│   └── data/                             # Mock data
│       ├── mockAlerts.js
│       ├── mockDashboard.js
│       ├── mockLogs.js
│       ├── mockModels.js
│       └── mockServices.js
├── public/                               # Static assets
├── vite.config.js                        # Vite build configuration
├── eslint.config.js                      # ESLint configuration
├── package.json                          # Project dependencies
├── Dockerfile                            # Multi-stage build (Node 20, Nginx)
├── index.html                            # HTML template
└── README.md                             # This file
```

---

## 🚀 Quick Start

### Development Environment

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173/` with hot module reloading.

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t api-monitoring-frontend .
```

### Run with Docker

```bash
# Run on port 8080
docker run -d \
  -p 8080:80 \
  --name api-monitoring-frontend \
  api-monitoring-frontend
```

Access at: `http://localhost:8080`

### Docker Compose (Full Stack)

```bash
cd infrastructure/docker
docker compose up -d
```

This deploys:
- Frontend on port 8080 (Nginx)
- Backend on port 8081 (Spring Boot)
- OpenSearch Dashboards on port 5601

---

## 📦 Key Dependencies

### Framework & Libraries
- **React 18+** - UI framework
- **React Router** - Client-side routing
- **Vite** - Build tool (ESM bundler, faster than Webpack)
- **ESLint** - Code quality & linting

### Development Tools
- **npm** - Package manager
- **Nginx Alpine** - Web server in Docker

---

## 🎯 Available Scripts

| Command | Description |
|---------|-------------|
| `npm install` | Install dependencies |
| `npm run dev` | Start development server (port 5173) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint code quality checks |

---

## 🛠️ Configuration

### Backend API Connection

The frontend connects to the backend API at:
- **Development**: `http://localhost:8081` (via proxy in vite.config.js)
- **Docker**: `http://api-monitoring-backend:8081`

Modify `vite.config.js` to change backend URL:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8081',
    changeOrigin: true
  }
}
```

### Theme Configuration

Edit `src/theme.js` to customize:
- Colors
- Typography
- Component styling

---

## 🏗️ Build Optimization

The Dockerfile uses a **multi-stage build** for optimal image size:

1. **Builder stage** - Installs dependencies and builds with Node.js 20
2. **Runtime stage** - Serves with lightweight Nginx Alpine

```dockerfile
FROM node:20-alpine AS builder
# ... build steps ...
FROM nginx:alpine
# ... serve with Nginx ...
```

Resulting image: ~50MB (vs 500MB+ with Node in production)

---

## 📊 Pages & Features

### Dashboard
- Real-time metrics visualization
- API health status
- Service overview
- Quick actions

### Alerts
- List of active/resolved alerts
- Filter by severity & service
- Alert details & history
- Custom alert creation

### Logs
- Centralized log viewing
- Full-text search
- Timeline visualization
- Log level filtering

### Services
- All monitored services
- Service health status
- Endpoint metrics
- Performance trends

### Models
- ML model management
- Training history
- Prediction accuracy
- Model versioning

### Settings
- Configuration management
- User preferences
- Notification settings
- System administration

---

## 🐛 Troubleshooting

### Dependencies Installation Issues

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall dependencies
npm install
```

### Port 5173 Already in Use (Development)

```bash
# Find process using port 5173
lsof -i :5173

# Kill the process
kill -9 <PID>

# Or use different port
npm run dev -- --port 3000
```

### Docker Build Fails

```bash
# Check Node version
node --version  # Should be 20.x

# Rebuild Docker image without cache
docker build --no-cache -t api-monitoring-frontend .

# Check logs
docker logs api-monitoring-frontend
```

### Backend Connection Issues

```bash
# Test backend health
curl http://localhost:8081/health

# Check network connectivity
docker network ls
docker network inspect docker_monitoring-net
```

---

## 📝 ESLint Configuration

Project includes ESLint rules in `eslint.config.js`. Run checks with:

```bash
npm run lint
```

---

## 🔄 CI/CD

### Docker Multi-Stage Build
- Optimized for production deployment
- Minimal final image size
- Fast startup time

### Environment Variables (Docker)

```bash
# Set backend URL for Docker builds
ENV REACT_APP_API_URL=http://api-monitoring-backend:8081
```

---

## 🌐 Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

---

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [React Router Guide](https://reactrouter.com/)
- [ESLint Rules](https://eslint.org/docs/rules/)

---

## ⚙️ Version Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Node.js | 20.x LTS | 20.x.x or higher |
| npm | 10.x | Included with Node.js 20.x |
| React | 18+ | Latest stable |
| Vite | 5.x+ | Latest stable |
| Nginx | Alpine | Ultra-lightweight |
| Docker | 29.x+ | 29.1.3+ |

---

## 📝 License

[Your License Here]
