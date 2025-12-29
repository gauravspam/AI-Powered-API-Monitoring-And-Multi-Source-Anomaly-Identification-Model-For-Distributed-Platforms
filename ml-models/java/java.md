## Java Backend APIs (Port 8080)

These are the APIs your Java backend exposes for React frontend and internal use.

### 1. Single Anomaly Detection
**POST** `http://localhost:8080/api/v1/anomalies/detect`

**Request JSON:**
```json
{
  "api_name": "payment_service",
  "response_time": 950.5,
  "status_code": 500,
  "request_count": 1200,
  "error_rate": 0.35,
  "cpu_usage": 87.5,
  "memory_usage": 79.3,
  "network_io": 450.2,
  "disk_io": 220.1,
  "hour_of_day": 19,
  "day_of_week": 1,
  "timestamp": "2025-12-29T18:55:00"
}
```

**Response JSON:**
```json
{
  "api_name": "payment_service",
  "stage": 2,
  "model": "MSIF-LSTM",
  "anomaly_score": 0.68,
  "stage2_score": 0.83,
  "final_anomaly_score": 0.755,
  "status": "ANOMALY_DETECTED",
  "severity": "HIGH",
  "confidence": 0.51,
  "timestamp": "2025-12-29T18:55:01"
}
```

***

### 2. Batch Anomaly Detection
**POST** `http://localhost:8080/api/v1/anomalies/detect-batch`

**Request JSON:**
```json
[
  {
    "api_name": "payment_service",
    "response_time": 950.5,
    "status_code": 500,
    "request_count": 1200,
    "error_rate": 0.35,
    "cpu_usage": 87.5,
    "memory_usage": 79.3,
    "network_io": 450.2,
    "disk_io": 220.1,
    "hour_of_day": 19,
    "day_of_week": 1
  },
  {
    "api_name": "user_service",
    "response_time": 120.3,
    "status_code": 200,
    "request_count": 45,
    "error_rate": 0.02,
    "cpu_usage": 25.1,
    "memory_usage": 34.2,
    "network_io": 12.5,
    "disk_io": 3.1,
    "hour_of_day": 19,
    "day_of_week": 1
  }
]
```

**Response JSON:**
```json
[
  {
    "api_name": "payment_service",
    "stage": 2,
    "status": "ANOMALY_DETECTED",
    "severity": "HIGH",
    "final_anomaly_score": 0.755
  },
  {
    "api_name": "user_service",
    "stage": 1,
    "status": "NORMAL",
    "severity": "INFO",
    "final_anomaly_score": 0.12
  }
]
```

***

### 3. Get Recent Anomalies
**GET** `http://localhost:8080/api/v1/anomalies/recent/payment_service`

**Response JSON:**
```json
[
  {
    "api_name": "payment_service",
    "stage": 2,
    "status": "ANOMALY_DETECTED",
    "severity": "HIGH",
    "final_anomaly_score": 0.755,
    "timestamp": "2025-12-29T18:55:01"
  },
  {
    "api_name": "payment_service",
    "stage": 1,
    "status": "SUSPICIOUS",
    "severity": "LOW",
    "final_anomaly_score": 0.45,
    "timestamp": "2025-12-29T18:54:30"
  }
]
```

***

### 4. Get API Statistics
**GET** `http://localhost:8080/api/v1/anomalies/statistics/payment_service`

**Response JSON:**
```json
{
  "api_name": "payment_service",
  "total_logs": 1250,
  "normal_count": 1080,
  "suspicious_count": 120,
  "anomaly_count": 50,
  "avg_anomaly_score": 0.23,
  "peak_hour": 19,
  "last_24h_anomalies": 12,
  "alerts_triggered": 8
}
```

***

### 5. Health Check
**GET** `http://localhost:8080/api/v1/anomalies/health`

**Response JSON:**
```json
{
  "status": "healthy",
  "pythonServiceStatus": true,
  "databaseStatus": true,
  "totalApisMonitored": 5,
  "activeAlerts": 2
}
```

***

## Python Model APIs (Port 8000) 
*(Java calls these internally)*

### 1. Direct Python Anomaly Detection
**POST** `http://localhost:8000/api/detect-anomaly`

**Request JSON:** (Same as Java single detection)

**Response JSON:**
```json
{
  "success": true,
  "data": {
    "stage": 2,
    "model": "MSIF-LSTM",
    "anomaly_score": 0.68,
    "stage2_model": "PLE-GRU",
    "stage2_score": 0.83,
    "final_anomaly_score": 0.755,
    "status": "ANOMALY_DETECTED",
    "severity": "HIGH",
    "confidence": 0.51
  }
}
```

### 2. Python Health Check
**GET** `http://localhost:8000/health`

**Response JSON:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "timestamp": "2025-12-29T18:55:01"
}
```

### 3. Python Model Info
**GET** `http://localhost:8000/api/model-info`

**Response JSON:**
```json
{
  "stage1_model": "MSIF-LSTM",
  "stage2_model": "PLE-GRU",
  "confidence_threshold_stage1": 0.3,
  "confidence_threshold_stage2": 0.7,
  "features": 10,
  "description": "Two-stage anomaly detection system"
}
```

***

## How Your React Frontend Uses These

**For real-time monitoring dashboard:**
```javascript
// Send new log → get anomaly result instantly
POST /api/v1/anomalies/detect

// Show recent anomalies table
GET /api/v1/anomalies/recent/payment_service

// Show statistics cards
GET /api/v1/anomalies/statistics/payment_service

// Health status indicator
GET /api/v1/anomalies/health
```

**For batch processing (multiple logs):**
```javascript
// Process 100 logs at once
POST /api/v1/anomalies/detect-batch
```

***

## Complete Workflow Summary

```
React Frontend ──→ POST /api/v1/anomalies/detect ──→ Java Backend
                                                              │
                                                              ▼
                                                    Python Models
                                                    (MSIF-LSTM → PLE-GRU)
                                                              │
                                                              ▼
                                                    Response with anomaly score
                                                              │
                                                              ▼
React Frontend ←─── 200 OK with results ←─── Java Backend
```
