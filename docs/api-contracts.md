### GET /api/overview
Response:
{
  "totalRequests": number,
  "errorRate": number,          // percentage
  "anomaliesLast24h": number,
  "avgLatencyMs": number
}

### GET /api/anomalies
Response:
[
  {
    "id": string,
    "service": string,
    "environment": "prod" | "staging" | "dev",
    "severity": "low" | "medium" | "high",
    "timestamp": string (ISO-8601),
    "message": string,
    "score": number
  }
]
