import requests
import json

BASE_URL = "http://localhost:9000"

print("=" * 60)
print("TESTING MULTI-MODALITY ANOMALY DETECTION")
print("=" * 60)

# Test 1: Multimodal endpoint with all 3 modalities
print("\n[Test 1] POST /predict/multimodal")
payload = {
    "metrics": 0.8,
    "logs": 0.6,
    "traces": 0.7
}
try:
    response = requests.post(f"{BASE_URL}/predict/multimodal", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Normal values (low anomaly)
print("\n[Test 2] Normal values")
payload = {
    "metrics": 0.1,
    "logs": 0.1,
    "traces": 0.1
}
try:
    response = requests.post(f"{BASE_URL}/predict/multimodal", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: High values (should trigger ANOMALY)
print("\n[Test 3] High anomaly values")
payload = {
    "metrics": 0.9,
    "logs": 0.85,
    "traces": 0.95
}
try:
    response = requests.post(f"{BASE_URL}/predict/multimodal", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Main /predict endpoint
print("\n[Test 4] POST /predict (rule-based fallback)")
payload = {
    "response_time": 500,
    "status_code": 500,
    "cpu_usage": 80,
    "memory_usage": 50,
    "error_rate": 0.3,
    "request_count": 100
}
try:
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 5: Health check
print("\n[Test 5] GET /health")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED!")
print("=" * 60)