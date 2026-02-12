import json

import requests


def test_predict_endpoint():
    """Test /v1/predict with sample payload"""

    payload = {
        "context": {
            "service_name": "test-service",
            "window_start_ms": 1707648000000,
            "window_end_ms": 1707648060000
        },
        "metrics": [
            {"name": "cpu_usage", "values": [0.7, 0.8, 0.75]}
        ],
        "logs": [
            {"timestamp": 1707648010000, "level": "ERROR", "template": "Connection timeout"}
        ],
        "traces": [
            {
                "trace_id": "test123",
                "span_id": "span1",
                "service": "api",
                "operation": "GET /test",
                "duration_ms": 150,
                "status_code": 200,
                "is_error": False
            }
        ]
    }

    response = requests.post(
        "http://localhost:9000/v1/predict",
        json=payload,
        timeout=5
    )

    assert response.status_code == 200

    result = response.json()
    assert "status" in result
    assert "final_score" in result
    assert result["final_score"] >= 0 and result["final_score"] <= 1
    assert result["processing_time_ms"] < 100

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    test_predict_endpoint()
