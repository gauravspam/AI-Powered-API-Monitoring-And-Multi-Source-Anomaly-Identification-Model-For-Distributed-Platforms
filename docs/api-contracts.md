### GET /api/overview
Response:
{
  "totalLogs": 12345,
  "services": [
    { "name": "demo-service", "count": 1000 },
    { "name": "billing-api", "count": 500 }
  ],
  "lastLogTimestamp": 1766239768858
}

### GET /api/anomalies
Response:
[
  {
  "service": "demo-service",
  "level": "ERROR",
  "message": "Request timeout",
  "timestamp": 1766239768858
  }
]
