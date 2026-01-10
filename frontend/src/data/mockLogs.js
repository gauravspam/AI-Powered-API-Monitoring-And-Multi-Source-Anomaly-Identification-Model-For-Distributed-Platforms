// Mock data for Logs page
// http://localhost:8080/api/logs/streams
export const logStreams = [
  {
    id: 1,
    source: 'Log4j',
    environment: 'AWS',
    serviceName: 'auth-service',
    ingestionLagSec: 2.3,
    status: 'healthy',
  },
  {
    id: 2,
    source: 'OpenTelemetry',
    environment: 'GCP',
    serviceName: 'payment-gateway',
    ingestionLagSec: 1.8,
    status: 'healthy',
  },
  {
    id: 3,
    source: 'Filebeat',
    environment: 'Azure',
    serviceName: 'inventory-service',
    ingestionLagSec: 45.2,
    status: 'delayed',
  },
  {
    id: 4,
    source: 'Log4j',
    environment: 'On Prem',
    serviceName: 'notification-service',
    ingestionLagSec: 3.1,
    status: 'healthy',
  },
  {
    id: 5,
    source: 'OpenTelemetry',
    environment: 'Multi Cloud',
    serviceName: 'analytics-api',
    ingestionLagSec: 5.7,
    status: 'healthy',
  },
];

// http://localhost:8080/api/logs/events
let events = [
  {
    "id": 1,
    "timestamp": "2026-01-10T18:22:48.758Z",
    "level": "INFO",
    "environment": "Azure",
    "serviceName": "payment-gateway",
    "message": "Background job completed",
    "correlationId": "corr-b936mj",
    "isAnomalyFlagged": false
  },
  {
    "id": 2,
    "timestamp": "2026-01-10T18:20:48.758Z",
    "level": "INFO",
    "environment": "On Prem",
    "serviceName": "analytics-api",
    "message": "Request processed successfully",
    "correlationId": "corr-5bd7t7",
    "isAnomalyFlagged": false
  },
  {
    "id": 3,
    "timestamp": "2026-01-10T18:18:48.758Z",
    "level": "ERROR",
    "environment": "On Prem",
    "serviceName": "user-profile",
    "message": "Authentication token validated",
    "correlationId": "corr-zsduaa",
    "isAnomalyFlagged": false
  },
  {
    "id": 4,
    "timestamp": "2026-01-10T18:16:48.758Z",
    "level": "INFO",
    "environment": "Azure",
    "serviceName": "auth-service",
    "message": "Invalid request payload received",
    "correlationId": "corr-fstjc",
    "isAnomalyFlagged": false
  },
  {
    "id": 5,
    "timestamp": "2026-01-10T18:14:48.758Z",
    "level": "ERROR",
    "environment": "AWS",
    "serviceName": "user-profile",
    "message": "Memory usage at 75% capacity",
    "correlationId": "corr-f5wz98",
    "isAnomalyFlagged": false
  },
  {
    "id": 6,
    "timestamp": "2026-01-10T18:12:48.758Z",
    "level": "ERROR",
    "environment": "GCP",
    "serviceName": "analytics-api",
    "message": "Request processed successfully",
    "correlationId": "corr-2m3bca",
    "isAnomalyFlagged": false
  },
  {
    "id": 7,
    "timestamp": "2026-01-10T18:10:48.758Z",
    "level": "ERROR",
    "environment": "On Prem",
    "serviceName": "user-profile",
    "message": "Database connection pool exhausted",
    "correlationId": "corr-zfeap6",
    "isAnomalyFlagged": false
  },
  {
    "id": 8,
    "timestamp": "2026-01-10T18:08:48.758Z",
    "level": "ERROR",
    "environment": "On Prem",
    "serviceName": "notification-service",
    "message": "Downstream service timeout",
    "correlationId": "corr-86nsbv",
    "isAnomalyFlagged": false
  },
  {
    "id": 9,
    "timestamp": "2026-01-10T18:06:48.758Z",
    "level": "ERROR",
    "environment": "AWS",
    "serviceName": "payment-gateway",
    "message": "Circuit breaker opened for downstream service",
    "correlationId": "corr-3lcbfr",
    "isAnomalyFlagged": false
  },
  {
    "id": 10,
    "timestamp": "2026-01-10T18:04:48.758Z",
    "level": "INFO",
    "environment": "Multi Cloud",
    "serviceName": "notification-service",
    "message": "Background job completed",
    "correlationId": "corr-i3aapg",
    "isAnomalyFlagged": false
  },
  {
    "id": 11,
    "timestamp": "2026-01-10T18:02:48.758Z",
    "level": "WARN",
    "environment": "Multi Cloud",
    "serviceName": "notification-service",
    "message": "API rate limit approaching threshold",
    "correlationId": "corr-mky0zp",
    "isAnomalyFlagged": false
  },
  {
    "id": 12,
    "timestamp": "2026-01-10T18:00:48.758Z",
    "level": "INFO",
    "environment": "Azure",
    "serviceName": "analytics-api",
    "message": "Invalid request payload received",
    "correlationId": "corr-gwclt",
    "isAnomalyFlagged": false
  },
  {
    "id": 13,
    "timestamp": "2026-01-10T17:58:48.758Z",
    "level": "INFO",
    "environment": "AWS",
    "serviceName": "user-profile",
    "message": "Background job completed",
    "correlationId": "corr-k2d6i",
    "isAnomalyFlagged": false
  },
  {
    "id": 14,
    "timestamp": "2026-01-10T17:56:48.758Z",
    "level": "WARN",
    "environment": "On Prem",
    "serviceName": "payment-gateway",
    "message": "Downstream service timeout",
    "correlationId": "corr-wox15",
    "isAnomalyFlagged": false
  },
  {
    "id": 15,
    "timestamp": "2026-01-10T17:54:48.758Z",
    "level": "WARN",
    "environment": "Azure",
    "serviceName": "notification-service",
    "message": "Authentication token validated",
    "correlationId": "corr-yvk0dl",
    "isAnomalyFlagged": false
  },
  {
    "id": 16,
    "timestamp": "2026-01-10T17:52:48.758Z",
    "level": "ERROR",
    "environment": "Azure",
    "serviceName": "analytics-api",
    "message": "Downstream service timeout",
    "correlationId": "corr-azo26i",
    "isAnomalyFlagged": false
  },
  {
    "id": 17,
    "timestamp": "2026-01-10T17:50:48.758Z",
    "level": "INFO",
    "environment": "On Prem",
    "serviceName": "notification-service",
    "message": "Database connection pool exhausted",
    "correlationId": "corr-l8pqkf",
    "isAnomalyFlagged": false
  },
  {
    "id": 18,
    "timestamp": "2026-01-10T17:48:48.758Z",
    "level": "INFO",
    "environment": "AWS",
    "serviceName": "notification-service",
    "message": "API rate limit approaching threshold",
    "correlationId": "corr-xlj4a9",
    "isAnomalyFlagged": true
  },
  {
    "id": 19,
    "timestamp": "2026-01-10T17:46:48.758Z",
    "level": "WARN",
    "environment": "AWS",
    "serviceName": "notification-service",
    "message": "Circuit breaker opened for downstream service",
    "correlationId": "corr-4f6zxe",
    "isAnomalyFlagged": false
  },
  {
    "id": 20,
    "timestamp": "2026-01-10T17:44:48.758Z",
    "level": "WARN",
    "environment": "AWS",
    "serviceName": "analytics-api",
    "message": "Request processed successfully",
    "correlationId": "corr-g3zfq9",
    "isAnomalyFlagged": false
  }
]









// Generate log events for timeline
const generateLogEvents = () => {
  const services = ['auth-service', 'payment-gateway', 'user-profile', 'notification-service', 'analytics-api'];
  const environments = ['AWS', 'GCP', 'Azure', 'On Prem', 'Multi Cloud'];
  const levels = ['INFO', 'WARN', 'ERROR'];
  const messages = [
    'Request processed successfully',
    'Database connection pool exhausted',
    'API rate limit approaching threshold',
    'Cache miss - fallback to database',
    'Authentication token validated',
    'Downstream service timeout',
    'Memory usage at 75% capacity',
    'Background job completed',
    'Invalid request payload received',
    'Circuit breaker opened for downstream service',
  ];

  const events = [];
  const now = new Date();

  for (let i = 0; i < 20; i++) {
    const timestamp = new Date(now.getTime() - i * 120000).toISOString();
    const level = levels[Math.floor(Math.random() * levels.length)];
    const isAnomalyFlagged = Math.random() > 0.85;

    events.push({
      id: i + 1,
      timestamp,
      level,
      environment: environments[Math.floor(Math.random() * environments.length)],
      serviceName: services[Math.floor(Math.random() * services.length)],
      message: messages[Math.floor(Math.random() * messages.length)],
      correlationId: `corr-${Math.random().toString(36).substring(7)}`,
      isAnomalyFlagged,
    });
  }

  return events;
};

export const logEvents = generateLogEvents();
