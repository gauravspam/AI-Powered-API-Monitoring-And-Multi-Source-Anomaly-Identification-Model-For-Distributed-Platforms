import requests
import json

print("=" * 60)
print("MULTIMODAL ANOMALY DETECTION TESTS")
print("=" * 60)

tests = [
    # Test 1: Metrics only (1 modality) - Normal
    {
        "name": "1. Metrics Only - Normal",
        "data": {"metrics": {"cpu_usage": 30, "memory_usage": 40, "response_time_ms": 50, "error_rate": 0}}
    },
    # Test 2: Metrics only - High CPU
    {
        "name": "2. Metrics Only - High CPU",
        "data": {"metrics": {"cpu_usage": 95, "memory_usage": 50, "response_time_ms": 500, "error_rate": 5}}
    },
    # Test 3: Logs only (1 modality) - Normal
    {
        "name": "3. Logs Only - Normal",
        "data": {"logs": [{"level": "INFO", "message": "Request processed successfully"}]}
    },
    # Test 4: Logs only - Error
    {
        "name": "4. Logs Only - Error",
        "data": {"logs": [{"level": "ERROR", "message": "Database connection timeout"}]}
    },
    # Test 5: Traces only (1 modality) - Normal
    {
        "name": "5. Traces Only - Normal",
        "data": {"traces": [{"duration": 50, "status_code": 200}]}
    },
    # Test 6: Traces only - Slow
    {
        "name": "6. Traces Only - Slow",
        "data": {"traces": [{"duration": 5000, "status_code": 503}]}
    },
    # Test 7: Metrics + Logs (2 modalities)
    {
        "name": "7. Metrics + Logs - Normal",
        "data": {
            "metrics": {"cpu_usage": 40, "memory_usage": 50, "response_time_ms": 100, "error_rate": 1},
            "logs": [{"level": "INFO", "message": "Health check OK"}]
        }
    },
    # Test 8: Metrics + Logs - Anomaly
    {
        "name": "8. Metrics + Logs - Anomaly",
        "data": {
            "metrics": {"cpu_usage": 95, "memory_usage": 90, "response_time_ms": 3000, "error_rate": 40},
            "logs": [{"level": "CRITICAL", "message": "OutOfMemoryError"}]
        }
    },
    # Test 9: Metrics + Traces (2 modalities)
    {
        "name": "9. Metrics + Traces - Normal",
        "data": {
            "metrics": {"cpu_usage": 50, "memory_usage": 60, "response_time_ms": 150, "error_rate": 2},
            "traces": [{"duration": 100, "status_code": 200}]
        }
    },
    # Test 10: Logs + Traces (2 modalities)
    {
        "name": "10. Logs + Traces - Anomaly",
        "data": {
            "logs": [{"level": "ERROR", "message": "Connection refused"}],
            "traces": [{"duration": 8000, "status_code": 500}]
        }
    },
    # Test 11: All 3 modalities - Normal
    {
        "name": "11. All 3 Modalities - Normal",
        "data": {
            "metrics": {"cpu_usage": 45, "memory_usage": 55, "response_time_ms": 120, "error_rate": 1},
            "logs": [{"level": "INFO", "message": "Request completed"}],
            "traces": [{"duration": 80, "status_code": 200}]
        }
    },
    # Test 12: All 3 modalities - Critical
    {
        "name": "12. All 3 Modalities - Critical",
        "data": {
            "metrics": {"cpu_usage": 99, "memory_usage": 98, "response_time_ms": 10000, "error_rate": 90},
            "logs": [{"level": "CRITICAL", "message": "System down - FATAL ERROR"}],
            "traces": [{"duration": 15000, "status_code": 503}]
        }
    },
]

for test in tests:
    try:
        r = requests.post('http://localhost:9000/predict/flexible', json=test["data"], timeout=10)
        res = r.json()
        print(f"\n{test['name']}")
        print(f"  Modalities: {res.get('modalities_present', 'N/A')}")
        print(f"  Score: {res.get('final_score', 'N/A')}")
        print(f"  Severity: {res.get('severity', 'N/A')}")
        print(f"  MSIF: {res.get('msif_score', 'N/A')}, PLE: {res.get('ple_score', 'N/A')}")
    except Exception as e:
        print(f"\n{test['name']}")
        print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)