// Mock data for Dashboard page
import {
  Speed as SpeedIcon,
  ErrorOutline as ErrorIcon,
  Warning as WarningIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';

export const kpiCards = [
  {
    id: 1,
    label: 'Total Requests',
    value: '2.4M',
    trend: 12.5,
    trendDirection: 'up',
    unit: '/hour',
    icon: SpeedIcon,
  },
  {
    id: 2,
    label: 'Error Rate',
    value: '2.3',
    trend: -8.2,
    trendDirection: 'down',
    unit: '%',
    icon: ErrorIcon,
  },
  {
    id: 3,
    label: 'Anomaly Rate',
    value: '0.8',
    trend: 15.3,
    trendDirection: 'up',
    unit: '%',
    icon: WarningIcon,
  },
  {
    id: 4,
    label: 'Avg Latency',
    value: '145',
    trend: -5.1,
    trendDirection: 'down',
    unit: 'ms',
    icon: TimerIcon,
  },
];

export const environmentSummary = [
  {
    id: 1,
    name: 'On Prem',
    status: 'healthy',
    uptime: 99.98,
    errorRate: 0.5,
    anomalyCount: 3,
    requestPerMin: 45000,
  },
  {
    id: 2,
    name: 'AWS',
    status: 'healthy',
    uptime: 99.99,
    errorRate: 0.3,
    anomalyCount: 2,
    requestPerMin: 78000,
  },
  {
    id: 3,
    name: 'GCP',
    status: 'degraded',
    uptime: 99.85,
    errorRate: 2.1,
    anomalyCount: 8,
    requestPerMin: 52000,
  },
  {
    id: 4,
    name: 'Azure',
    status: 'healthy',
    uptime: 99.96,
    errorRate: 0.7,
    anomalyCount: 4,
    requestPerMin: 61000,
  },
  {
    id: 5,
    name: 'Multi Cloud',
    status: 'healthy',
    uptime: 99.94,
    errorRate: 1.2,
    anomalyCount: 6,
    requestPerMin: 34000,
  },
];

export const recentAnomalies = [
  {
    id: 1,
    serviceName: 'auth-service',
    endpoint: '/api/v1/login',
    environment: 'AWS',
    severity: 'critical',
    type: 'latency_spike',
    detectedAt: '2025-01-20T10:35:22Z',
    status: 'investigating',
    score: 0.94,
  },
  {
    id: 2,
    serviceName: 'payment-gateway',
    endpoint: '/api/v2/process',
    environment: 'GCP',
    severity: 'high',
    type: 'error_burst',
    detectedAt: '2025-01-20T10:28:15Z',
    status: 'open',
    score: 0.87,
  },
  {
    id: 3,
    serviceName: 'user-profile',
    endpoint: '/api/v1/users/:id',
    environment: 'Azure',
    severity: 'medium',
    type: 'throughput_drop',
    detectedAt: '2025-01-20T10:15:43Z',
    status: 'mitigated',
    score: 0.72,
  },
  {
    id: 4,
    serviceName: 'notification-service',
    endpoint: '/api/v1/send',
    environment: 'On Prem',
    severity: 'low',
    type: 'auth_failure',
    detectedAt: '2025-01-20T09:58:31Z',
    status: 'investigating',
    score: 0.65,
  },
  {
    id: 5,
    serviceName: 'analytics-api',
    endpoint: '/api/v3/events',
    environment: 'Multi Cloud',
    severity: 'high',
    type: 'latency_spike',
    detectedAt: '2025-01-20T09:42:18Z',
    status: 'open',
    score: 0.89,
  },
];

// Generate time series data for the last hour
const generateTrafficSeries = () => {
  const data = [];
  const now = new Date();
  
  for (let i = 60; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60000).toISOString();
    data.push({
      timestamp,
      requestsPerSec: Math.floor(Math.random() * 5000) + 35000 + Math.sin(i / 10) * 3000,
      errorRate: Math.random() * 3 + 0.5,
      anomalyScore: Math.random() * 0.3 + (i < 10 ? 0.6 : 0.1),
    });
  }
  
  return data;
};

export const trafficSeries = generateTrafficSeries();
