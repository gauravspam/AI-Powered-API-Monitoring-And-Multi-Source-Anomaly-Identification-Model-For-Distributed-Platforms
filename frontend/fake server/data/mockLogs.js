// Mock data for Logs page

const logStreams = [
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

const logEvents = generateLogEvents();
module.exports = { logEvents, logStreams };