# Data Flow & Integration Guide - Option B Architecture

**Date**: March 8, 2026  
**Purpose**: Practical integration patterns for emitting logs, metrics, and traces to the Option B observability stack

---

## 🎯 Quick Start Integration Matrix

| You Want To... | Use This | Send To | Format |
|----------------|----------|---------|--------|
| **Send logs** | Fluentd Forward library | `fluentd:24224` | JSON via forward protocol |
| **Send logs (simple)** | HTTP POST | `http://fluentd:9880/<tag>` | JSON |
| **Send metrics** | HTTP POST | `http://backend:8080/api/metrics` | JSON REST API |
| **Send traces** | HTTP POST | `http://backend:8080/api/traces/ingest` | JSON REST API |
| **Query logs** | OpenSearch API | `http://opensearch:9200/logs-*/_search` | OpenSearch Query DSL |
| **Query metrics** | PostgreSQL | `jdbc:postgresql://postgres:5432/api_monitoring` | SQL |
| **Query traces** | PostgreSQL | `jdbc:postgresql://postgres:5432/api_monitoring` | SQL |

---

## 📤 Emitting Logs (Path: Service → Fluentd → OpenSearch)

### Method 1: Fluentd Forward Protocol (Recommended for Production)

**Why**: Efficient binary protocol, automatic buffering, reconnection logic

#### Java (Spring Boot) - Using fluent-logger-java

**1. Add dependency** (`build.gradle`):
```gradle
dependencies {
    implementation 'org.fluentd:fluent-logger:0.3.4'
}
```

**2. Configure logger**:
```java
import org.fluentd.logger.FluentLogger;

public class LogEmitter {
    private static final FluentLogger LOG = FluentLogger.getLogger("app.backend", "fluentd", 24224);
    
    public void logEvent(String userId, String action) {
        Map<String, Object> data = new HashMap<>();
        data.put("userId", userId);
        data.put("action", action);
        data.put("level", "INFO");
        data.put("timestamp", Instant.now().toString());
        
        LOG.log("user.action", data);
    }
}
```

**3. Output in Fluentd**: Tag will be `app.backend.user.action`

#### Python - Using fluent-logger-python

**1. Install**:
```bash
pip install fluent-logger
```

**2. Usage**:
```python
from fluent import sender
from fluent import event
import time

# Initialize sender
logger = sender.FluentSender('app.ml-service', host='fluentd', port=24224)

# Send log
logger.emit('prediction', {
    'model': 'fusion_v2',
    'accuracy': 0.95,
    'latency_ms': 123,
    'timestamp': int(time.time())
})

# Tag will be: app.ml-service.prediction
```

#### Node.js - Using fluent-logger

**1. Install**:
```bash
npm install fluent-logger
```

**2. Usage**:
```javascript
const FluentClient = require('fluent-logger').FluentClient;

const logger = new FluentClient('app.frontend', {
  host: 'fluentd',
  port: 24224,
  timeout: 3.0,
  reconnectInterval: 600000 // 10 minutes
});

// Send log
logger.emit('pageview', {
  page: '/dashboard',
  userId: 'user123',
  duration: 1234,
  timestamp: new Date().toISOString()
});

// Tag will be: app.frontend.pageview
```

---

### Method 2: HTTP Input (Easier for Testing/Scripting)

**Why**: Simple curl, no client library needed, good for scripts

#### cURL Example

```bash
curl -X POST http://fluentd:9880/app.test \
  -H "Content-Type: application/json" \
  -d '{
    "message": "User logged in",
    "userId": "user123",
    "level": "INFO",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

#### Python (requests library)

```python
import requests
import datetime

def send_log(tag, data):
    url = f"http://fluentd:9880/{tag}"
    data['timestamp'] = datetime.datetime.utcnow().isoformat() + 'Z'
    response = requests.post(url, json=data)
    return response.status_code == 200

# Usage
send_log('app.alerts', {
    'message': 'High CPU detected',
    'service': 'user-api',
    'cpuUsage': 95.2,
    'level': 'WARN'
})
```

#### JavaScript (fetch API)

```javascript
async function sendLog(tag, data) {
  const response = await fetch(`http://fluentd:9880/${tag}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...data,
      timestamp: new Date().toISOString()
    })
  });
  return response.ok;
}

// Usage
sendLog('app.errors', {
  message: 'Database connection failed',
  service: 'auth-service',
  level: 'ERROR',
  errorCode: 'DB_CONN_TIMEOUT'
});
```

---

### Method 3: Log File Collector (Fluentd tail input)

**Why**: Collect from existing log files without code changes

**Configure Fluentd** (add to `fluent.conf`):
```ruby
# Tail application log files
<source>
  @type tail
  @id input_tail_app
  
  path /var/log/app/*.log
  pos_file /fluentd/log/app.log.pos
  
  tag app.filebeat
  
  <parse>
    @type json
    time_key timestamp
    time_format %iso8601
  </parse>
</source>
```

**Mount volume** (update `docker-compose.yml`):
```yaml
fluentd:
  volumes:
    - ./fluent.conf:/fluentd/etc/fluent.conf:ro
    - fluentd_buffer:/fluentd/log
    - /path/to/app/logs:/var/log/app:ro  # Add this
```

---

## 📊 Emitting Metrics (Path: Service → Backend API → PostgreSQL)

### REST API Endpoint

**URL**: `POST http://backend:8080/api/metrics`

**Headers**:
```
Content-Type: application/json
```

**Payload Schema**:
```json
{
  "serviceName": "string (required)",
  "cpuUsage": "number (0-100)",
  "memoryUsage": "number (0-100)",
  "diskIoBytes": "integer",
  "networkIoBytes": "integer",
  "responseTimeMs": "integer",
  "requestCount": "integer",
  "errorRate": "number (0-1)",
  "timestamp": "ISO8601 string (optional, defaults to now)"
}
```

### Integration Examples

#### Java (Spring Boot) - Using RestTemplate

```java
@Service
public class MetricsEmitter {
    
    private final RestTemplate restTemplate;
    private final String metricsUrl = "http://backend:8080/api/metrics";
    
    @Autowired
    public MetricsEmitter(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    public void sendMetrics(String serviceName, double cpuUsage, double memoryUsage) {
        MetricPayload payload = MetricPayload.builder()
            .serviceName(serviceName)
            .cpuUsage(cpuUsage)
            .memoryUsage(memoryUsage)
            .responseTimeMs(null)
            .requestCount(null)
            .errorRate(null)
            .timestamp(Instant.now().toString())
            .build();
            
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(metricsUrl, payload, Map.class);
            if (response.getStatusCode().is2xxSuccessful()) {
                log.debug("Metrics sent successfully: {}", response.getBody());
            }
        } catch (Exception e) {
            log.error("Failed to send metrics", e);
        }
    }
}
```

#### Python (requests library)

```python
import requests
from datetime import datetime

class MetricsEmitter:
    def __init__(self, backend_url="http://backend:8080"):
        self.metrics_url = f"{backend_url}/api/metrics"
    
    def send_metrics(self, service_name, cpu_usage=None, memory_usage=None, 
                    response_time_ms=None, request_count=None, error_rate=None):
        payload = {
            "serviceName": service_name,
            "cpuUsage": cpu_usage,
            "memoryUsage": memory_usage,
            "responseTimeMs": response_time_ms,
            "requestCount": request_count,
            "errorRate": error_rate,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        try:
            response = requests.post(self.metrics_url, json=payload, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send metrics: {e}")
            return None

# Usage
emitter = MetricsEmitter()
emitter.send_metrics(
    service_name="ml-service",
    cpu_usage=45.2,
    memory_usage=62.8,
    response_time_ms=150
)
```

#### Node.js (axios library)

```javascript
const axios = require('axios');

class MetricsEmitter {
  constructor(backendUrl = 'http://backend:8080') {
    this.metricsUrl = `${backendUrl}/api/metrics`;
  }
  
  async sendMetrics({
    serviceName,
    cpuUsage = null,
    memoryUsage = null,
    responseTimeMs = null,
    requestCount = null,
    errorRate = null
  }) {
    const payload = {
      serviceName,
      cpuUsage,
      memoryUsage,
      responseTimeMs,
      requestCount,
      errorRate,
      timestamp: new Date().toISOString()
    };
    
    // Remove null values
    Object.keys(payload).forEach(key => 
      payload[key] === null && delete payload[key]
    );
    
    try {
      const response = await axios.post(this.metricsUrl, payload, {
        timeout: 5000,
        headers: { 'Content-Type': 'application/json' }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to send metrics:', error.message);
      return null;
    }
  }
}

// Usage
const emitter = new MetricsEmitter();
emitter.sendMetrics({
  serviceName: 'frontend',
  cpuUsage: 35.5,
  memoryUsage: 55.2,
  requestCount: 1200
});
```

#### Bash (cron job / monitoring script)

```bash
#!/bin/bash
# metrics-collector.sh - Run via cron every minute

SERVICE_NAME="system-monitor"
BACKEND_URL="http://backend:8080/api/metrics"

# Collect system metrics (Linux)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEMORY_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')

# Send to backend
curl -X POST "$BACKEND_URL" \
  -H "Content-Type: application/json" \
  -s -w "%{http_code}" \
  -d '{
    "serviceName": "'"$SERVICE_NAME"'",
    "cpuUsage": '"$CPU_USAGE"',
    "memoryUsage": '"$MEMORY_USAGE"',
    "timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"
  }'
```

---

## 🔍 Emitting Traces (Path: Service → Backend API → PostgreSQL)

### REST API Endpoint

**URL**: `POST http://backend:8080/api/traces/ingest`

**Headers**:
```
Content-Type: application/json
```

**Payload Schema**:
```json
{
  "traceId": "string (required)",
  "spanId": "string (required)",
  "parentSpanId": "string (optional)",
  "serviceName": "string (required)",
  "operationName": "string (required)",
  "startTime": "ISO8601 string (required)",
  "endTime": "ISO8601 string (required)",
  "duration": "integer (milliseconds, required)",
  "statusCode": "integer (HTTP status code, optional)",
  "tags": "object (key-value pairs, optional)",
  "logs": "array (span logs, optional)"
}
```

### Integration Examples

#### Java (Manual Tracing)

```java
@Service
public class TraceEmitter {
    
    private final RestTemplate restTemplate;
    private final String tracesUrl = "http://backend:8080/api/traces/ingest";
    
    public void traceOperation(String serviceName, String operationName, Runnable operation) {
        String traceId = UUID.randomUUID().toString();
        String spanId = UUID.randomUUID().toString();
        Instant startTime = Instant.now();
        
        int statusCode = 200;
        try {
            operation.run();
        } catch (Exception e) {
            statusCode = 500;
            throw e;
        } finally {
            Instant endTime = Instant.now();
            long duration = Duration.between(startTime, endTime).toMillis();
            
            TraceSpan span = TraceSpan.builder()
                .traceId(traceId)
                .spanId(spanId)
                .serviceName(serviceName)
                .operationName(operationName)
                .startTime(startTime.toString())
                .endTime(endTime.toString())
                .duration(duration)
                .statusCode(statusCode)
                .tags(Map.of("component", "service-layer"))
                .build();
                
            sendTrace(span);
        }
    }
    
    private void sendTrace(TraceSpan span) {
        try {
            restTemplate.postForEntity(tracesUrl, span, Map.class);
        } catch (Exception e) {
            log.error("Failed to send trace", e);
        }
    }
}

// Usage
@Autowired
private TraceEmitter tracer;

public void processOrder(String orderId) {
    tracer.traceOperation("order-service", "processOrder", () -> {
        // Business logic here
        orderRepository.save(order);
    });
}
```

#### Python (Decorator Pattern)

```python
import requests
import time
import uuid
from datetime import datetime
from functools import wraps

class TraceEmitter:
    def __init__(self, service_name, backend_url="http://backend:8080"):
        self.service_name = service_name
        self.traces_url = f"{backend_url}/api/traces/ingest"
    
    def trace(self, operation_name):
        """Decorator to trace function execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                trace_id = str(uuid.uuid4())
                span_id = str(uuid.uuid4())
                start_time = time.time()
                start_iso = datetime.utcnow().isoformat() + 'Z'
                
                status_code = 200
                error = None
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = 500
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    end_iso = datetime.utcnow().isoformat() + 'Z'
                    duration = int((end_time - start_time) * 1000)  # ms
                    
                    span = {
                        "traceId": trace_id,
                        "spanId": span_id,
                        "serviceName": self.service_name,
                        "operationName": operation_name,
                        "startTime": start_iso,
                        "endTime": end_iso,
                        "duration": duration,
                        "statusCode": status_code,
                        "tags": {
                            "function": func.__name__,
                            "error": error
                        } if error else {"function": func.__name__}
                    }
                    
                    self._send_trace(span)
            
            return wrapper
        return decorator
    
    def _send_trace(self, span):
        try:
            requests.post(self.traces_url, json=span, timeout=3)
        except Exception as e:
            print(f"Failed to send trace: {e}")

# Usage
tracer = TraceEmitter("ml-service")

@tracer.trace("predict_anomaly")
def predict_anomaly(data):
    # ML inference logic
    return {"anomaly": False, "score": 0.12}

result = predict_anomaly(some_data)  # Automatically traced
```

#### Node.js (Express Middleware)

```javascript
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

class TraceEmitter {
  constructor(serviceName, backendUrl = 'http://backend:8080') {
    this.serviceName = serviceName;
    this.tracesUrl = `${backendUrl}/api/traces/ingest`;
  }
  
  // Express middleware
  middleware() {
    return (req, res, next) => {
      const traceId = uuidv4();
      const spanId = uuidv4();
      const startTime = new Date();
      
      // Capture response
      const originalSend = res.send;
      res.send = function(data) {
        const endTime = new Date();
        const duration = endTime - startTime;
        
        const span = {
          traceId,
          spanId,
          serviceName: this.serviceName,
          operationName: `${req.method} ${req.path}`,
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
          duration,
          statusCode: res.statusCode,
          tags: {
            'http.method': req.method,
            'http.url': req.originalUrl,
            'http.status_code': res.statusCode
          }
        };
        
        this._sendTrace(span).catch(console.error);
        
        return originalSend.call(res, data);
      }.bind(this);
      
      next();
    };
  }
  
  async _sendTrace(span) {
    try {
      await axios.post(this.tracesUrl, span, { timeout: 3000 });
    } catch (error) {
      console.error('Failed to send trace:', error.message);
    }
  }
}

// Usage with Express
const express = require('express');
const app = express();

const tracer = new TraceEmitter('api-gateway');
app.use(tracer.middleware());

app.get('/users', (req, res) => {
  // Auto-traced
  res.json({ users: [] });
});
```

---

## 📥 Querying Data

### Query Logs (OpenSearch)

**Direct API**:
```bash
# Search all logs
curl -X GET "http://opensearch:9200/logs-*/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match": {"service": "user-api"}},
          {"range": {"@timestamp": {"gte": "now-1h"}}}
        ]
      }
    },
    "size": 100,
    "sort": [{"@timestamp": "desc"}]
  }'
```

**Via Backend API** (if implemented):
```bash
curl "http://backend:8080/api/logs/search?service=user-api&level=ERROR&limit=50"
```

### Query Metrics (PostgreSQL)

```sql
-- Recent metrics for a service
SELECT 
    service_name,
    cpu_usage_percent,
    memory_usage_percent,
    response_time_ms,
    metric_timestamp
FROM systemmetrics
WHERE service_name = 'user-api'
  AND metric_timestamp > NOW() - INTERVAL '1 hour'
ORDER BY metric_timestamp DESC;

-- Average metrics by service (last 24h)
SELECT 
    service_name,
    AVG(cpu_usage_percent) as avg_cpu,
    AVG(memory_usage_percent) as avg_memory,
    AVG(response_time_ms) as avg_response_time,
    COUNT(*) as metric_count
FROM systemmetrics
WHERE metric_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY service_name
ORDER BY avg_cpu DESC;
```

### Query Traces (PostgreSQL)

```sql
-- Recent traces
SELECT 
    trace_id,
    span_id,
    service_name,
    operation_name,
    duration,
    status_code,
    start_time
FROM distributedtraces
WHERE start_time > NOW() - INTERVAL '1 hour'
ORDER BY start_time DESC
LIMIT 100;

-- Slow operations (> 500ms duration)
SELECT 
    service_name,
    operation_name,
    AVG(duration) as avg_duration_ms,
    MAX(duration) as max_duration_ms,
    COUNT(*) as count
FROM distributedtraces
WHERE start_time > NOW() - INTERVAL '24 hours'
GROUP BY service_name, operation_name
HAVING AVG(duration) > 500
ORDER BY avg_duration_ms DESC;

-- Trace by ID (get all spans)
SELECT *
FROM distributedtraces
WHERE trace_id = 'your-trace-id-here'
ORDER BY start_time ASC;
```

---

## 🔗 Cross-Signal Correlation

### Example: Find logs related to slow traces

```sql
-- In PostgreSQL
WITH slow_traces AS (
  SELECT DISTINCT service_name, EXTRACT(EPOCH FROM start_time) as timestamp_epoch
  FROM distributedtraces
  WHERE duration > 1000  -- > 1 second
    AND start_time > NOW() - INTERVAL '1 hour'
)
SELECT 
  st.service_name,
  st.timestamp_epoch,
  -- Query OpenSearch via backend API or direct integration
FROM slow_traces st;
```

Then query OpenSearch:
```bash
# For each slow trace timestamp, query logs ±5 seconds
curl -X GET "http://opensearch:9200/logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match": {"service": "user-api"}},
          {"range": {"@timestamp": {
            "gte": "2026-03-08T10:30:00Z",
            "lte": "2026-03-08T10:30:10Z"
          }}}
        ]
      }
    }
  }'
```

---

## 🎓 Best Practices

### Logs
✅ **DO**:
- Use structured JSON logs
- Include timestamp, level, service name
- Add correlation IDs (trace ID, request ID)
- Use appropriate log levels (DEBUG, INFO, WARN, ERROR)

❌ **DON'T**:
- Log sensitive data (passwords, tokens, PII)
- Use unstructured plain text logs
- Log at DEBUG level in production without filtering

### Metrics
✅ **DO**:
- Send metrics at regular intervals (e.g., every 60 seconds)
- Include service name in every metric
- Use consistent units (bytes, milliseconds, percentages)
- Batch metrics when possible

❌ **DON'T**:
- Send metrics synchronously in request path (use async)
- Include high-cardinality tags (user IDs, session IDs)
- Emit metrics more than once per second per service

### Traces
✅ **DO**:
- Generate unique trace IDs per request
- Link spans with parent_span_id
- Measure duration accurately
- Include HTTP method, URL, status code in tags

❌ **DON'T**:
- Create spans for every function call (too verbose)
- Include large payloads in span tags
- Trace background jobs without context

---

## 📖 Reference

- **Fluentd Documentation**: https://docs.fluentd.org/
- **OpenSearch Query DSL**: https://opensearch.org/docs/latest/query-dsl/
- **PostgreSQL JSON Functions**: https://www.postgresql.org/docs/current/functions-json.html
- **Architecture**: [ARCHITECTURE_OPTION_B.md](ARCHITECTURE_OPTION_B.md)
