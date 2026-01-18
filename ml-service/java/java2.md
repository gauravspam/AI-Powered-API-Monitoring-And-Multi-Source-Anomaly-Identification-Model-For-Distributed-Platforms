## 🎯 **Complete Java Backend APIs Reference** (Port 8080)

**All APIs your React dashboard needs + their exact purpose**

***

## **1. Single Log Anomaly Detection** ⭐ **MOST IMPORTANT**
```
POST http://localhost:8080/api/v1/anomalies/detect
```
**Purpose:** Send **1 live log** → Get instant anomaly result (MSIF-LSTM → PLE-GRU)

**Request JSON:**
```json
{
  "api_name": "payment_service",
  "response_time": 950,
  "status_code": 500,
  "request_count": 1200,
  "error_rate": 0.35,
  "cpu_usage": 87.5,
  "memory_usage": 79.3,
  "network_io": 450.2,
  "disk_io": 220.1,
  "hour_of_day": 19,
  "day_of_week": 1,
  "timestamp": "2025-12-29T19:15:00"
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
  "timestamp": "2025-12-29T19:15:01"
}
```

***

## **2. Batch Log Processing** 
```
POST http://localhost:8080/api/v1/anomalies/detect-batch
```
**Purpose:** Send **100+ logs at once** → Get bulk anomaly results (faster)

**Request JSON:**
```json
[
  {
    "api_name": "payment_service",
    "response_time": 950,
    "status_code": 500,
    "error_rate": 0.35
  },
  {
    "api_name": "user_service", 
    "response_time": 120,
    "status_code": 200,
    "error_rate": 0.02
  }
]
```

**Response JSON:**
```json
[
  {
    "api_name": "payment_service",
    "status": "ANOMALY_DETECTED",
    "severity": "HIGH",
    "final_anomaly_score": 0.755
  },
  {
    "api_name": "user_service",
    "status": "NORMAL",
    "severity": "INFO",
    "final_anomaly_score": 0.12
  }
]
```

***

## **3. Recent Anomalies** ⭐ **For Alerts Dashboard**
```
GET http://localhost:8080/api/v1/anomalies/recent/{api_name}
```
**Purpose:** Get **last 100 anomalies** for specific API → **Your red/yellow alerts table**

**Example:** `GET http://localhost:8080/api/v1/anomalies/recent/payment_service`

**Response JSON:**
```json
[
  {
    "api_name": "payment_service",
    "status": "ANOMALY_DETECTED",
    "severity": "HIGH",
    "final_anomaly_score": 0.755,
    "stage": 2,
    "model": "MSIF-LSTM",
    "timestamp": "2025-12-29T19:15:01"
  },
  {
    "api_name": "payment_service",
    "status": "SUSPICIOUS",
    "severity": "LOW", 
    "final_anomaly_score": 0.45,
    "stage": 1,
    "timestamp": "2025-12-29T19:10:30"
  }
]
```

***

## **4. API Statistics** ⭐ **For Dashboard Cards**
```
GET http://localhost:8080/api/v1/anomalies/statistics/{api_name}
```
**Purpose:** **Summary stats** → Total anomalies, error rates, peak hours

**Example:** `GET http://localhost:8080/api/v1/anomalies/statistics/payment_service`

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
  "alerts_triggered": 8,
  "error_rate_trend": "increasing"
}
```

***

## **5. System Health** ⭐ **For Models Dashboard**
```
GET http://localhost:8080/api/v1/anomalies/health
```
**Purpose:** **Green status indicators** → Python models online? DB healthy?

**Response JSON:**
```json
{
  "status": "healthy",
  "pythonServiceStatus": true,
  "databaseStatus": true,
  "totalApisMonitored": 5,
  "activeAlerts": 2,
  "processingLatencyMs": 67,
  "uptimePercentage": 99.98
}
```

***

## **6. All Recent Anomalies** 
```
GET http://localhost:8080/api/v1/anomalies/recent-all?limit=50
```
**Purpose:** **Global alerts** → All services, not just 1 API

**Response JSON:** Same as #3 but mixed services

---

## **7. Model Information**
```
GET http://localhost:8080/api/v1/anomalies/model-info
```
**Purpose:** **Technical details** → Show MSIF-LSTM vs PLE-GRU specs

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

## **8. Clear Alerts** (Optional)
```
DELETE http://localhost:8080/api/v1/anomalies/{id}/acknowledge
```
**Purpose:** Mark alert as "handled" → Remove from dashboard

**Example:** `DELETE http://localhost:8080/api/v1/anomalies/123/acknowledge`

**Response:** `200 OK`

***

## 🎨 **React Dashboard Mapping**

```
📊 Alerts Table ← GET /api/v1/anomalies/recent/payment_service  (#3)
📈 Stats Cards  ← GET /api/v1/anomalies/statistics/payment_service (#4)  
🟢 Health Badge ← GET /api/v1/anomalies/health                 (#5)
🔴 Test Button  ← POST /api/v1/anomalies/detect                (#1)
```

## 🧪 **Quick Postman Test Sequence**

```bash
# 1. Health check first
curl http://localhost:8080/api/v1/anomalies/health

# 2. Send anomaly log (creates red alert)
curl -X POST http://localhost:8080/api/v1/anomalies/detect \
-H "Content-Type: application/json" \
-d '{"api_name":"payment_service","response_time":9500,"status_code":500,"error_rate":0.85}'

# 3. See it in alerts table
curl http://localhost:8080/api/v1/anomalies/recent/payment_service

# 4. Send normal log  
curl -X POST http://localhost:8080/api/v1/anomalies/detect \
-H "Content-Type: application/json" \
-d '{"api_name":"user_service","response_time":120,"status_code":200,"error_rate":0.01}'
```

## 🚀 **Production Usage Pattern**

```
Your Java Services ──→ POST /detect ──→ Python Analysis ──→ DB Storage
                           ↑
                    React Dashboard
                           ↓
                GET /recent + /statistics + /health
```
