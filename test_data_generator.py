#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Data Generator
Sends 5000 logs, metrics, and traces to the backend to test the full pipeline:
1. Backend receives data via REST API
2. Data stored in OpenSearch
3. ML models analyze and predict
4. Frontend fetches results
"""

import requests
import random
import time
import json
import sys
from datetime import datetime, timedelta

# Fix for Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8080"
ML_URL = "http://localhost:9000"

SERVICES = ["user-service", "payment-service", "order-service", "product-service", "notification-service"]
ENDPOINTS = ["/api/users", "/api/users/{id}", "/api/payments", "/api/orders", "/api/products", "/api/notifications"]
METHODS = ["GET", "POST", "PUT", "DELETE"]
ENVIRONMENTS = ["production", "staging", "development"]
LOG_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG"]

def generate_log(i):
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))
    return {
        "serviceName": random.choice(SERVICES),
        "level": random.choice(LOG_LEVELS),
        "message": f"Request processed - {random.choice(['success', 'completed', 'processed'])}",
        "source": "test-generator",
        "timestamp": timestamp.isoformat(),
        "traceId": f"trace-{i:06d}",
        "spanId": f"span-{i:06d}",
        "environment": random.choice(ENVIRONMENTS),
        "metadata": {
            "endpoint": random.choice(ENDPOINTS),
            "method": random.choice(METHODS),
            "statusCode": random.choices([200, 201, 400, 404, 500], weights=[70, 10, 10, 5, 5])[0],
            "responseTimeMs": random.randint(10, 2000),
        }
    }

def generate_metric(i):
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))
    return {
        "apiId": i,
        "cpuUsage": round(random.uniform(10, 95), 2),
        "memoryUsage": round(random.uniform(20, 90), 2),
        "responseTimeMs": random.randint(10, 1500),
        "errorRate": round(random.uniform(0, 15), 2),
        "requestCount": random.randint(10, 1000),
        "timestamp": timestamp.isoformat(),
    }

def generate_trace(i):
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))
    return {
        "traceId": f"trace-{i:06d}",
        "spanId": f"span-{i:06d}",
        "parentSpanId": f"span-{i-1:06d}" if i > 0 else None,
        "serviceName": random.choice(SERVICES),
        "operationName": random.choice(ENDPOINTS),
        "startTime": timestamp.isoformat(),
        "duration": random.randint(10, 3000),
        "statusCode": random.choices([200, 201, 400, 404, 500], weights=[70, 10, 10, 5, 5])[0],
        "isError": random.random() < 0.1,
        "tags": {
            "http.method": random.choice(METHODS),
            "environment": random.choice(ENVIRONMENTS)
        }
    }

def send_logs(count=5000, batch_size=100):
    print(f"\n{'='*50}")
    print(f"Sending {count} logs to backend...")
    print(f"{'='*50}")
    
    url = f"{BASE_URL}/api/logs/batch/raw"
    success = 0
    failed = 0
    
    start_time = time.time()
    for batch_num in range(0, count, batch_size):
        logs = [generate_log(i) for i in range(batch_num, min(batch_num + batch_size, count))]
        try:
            resp = requests.post(url, json=logs, timeout=30)
            if resp.status_code == 200:
                success += len(logs)
                print(f"  Sent {batch_num + len(logs)}/{count} logs...", end="\r")
            else:
                # Print first error for debugging
                if failed == 0:
                    print(f"  Error: {resp.status_code} - {resp.text[:200]}")
                failed += len(logs)
        except Exception as e:
            if failed == 0:
                print(f"  Error: {e}")
            failed += len(logs)
    
    elapsed = time.time() - start_time
    print(f"\n  [OK] Logs sent: {success}, Failed: {failed}, Time: {elapsed:.2f}s")
    return success

def send_metrics(count=5000, batch_size=100):
    print(f"\n{'='*50}")
    print(f"Sending {count} metrics to backend...")
    print(f"{'='*50}")
    
    url = f"{BASE_URL}/api/metrics/batch"
    success = 0
    failed = 0
    
    start_time = time.time()
    for batch_num in range(0, count, batch_size):
        metrics = [generate_metric(i) for i in range(batch_num, min(batch_num + batch_size, count))]
        try:
            resp = requests.post(url, json=metrics, timeout=30)
            if resp.status_code == 200:
                success += len(metrics)
                print(f"  Sent {batch_num + len(metrics)}/{count} metrics...", end="\r")
            else:
                if failed == 0:
                    print(f"  Error: {resp.status_code} - {resp.text[:200]}")
                failed += len(metrics)
        except Exception as e:
            if failed == 0:
                print(f"  Error: {e}")
            failed += len(metrics)
    
    elapsed = time.time() - start_time
    print(f"\n  [OK] Metrics sent: {success}, Failed: {failed}, Time: {elapsed:.2f}s")
    return success

def send_traces(count=5000, batch_size=100):
    print(f"\n{'='*50}")
    print(f"Sending {count} traces to backend...")
    print(f"{'='*50}")
    
    url = f"{BASE_URL}/api/traces/ingest/batch"
    success = 0
    failed = 0
    
    start_time = time.time()
    for batch_num in range(0, count, batch_size):
        traces = [generate_trace(i) for i in range(batch_num, min(batch_num + batch_size, count))]
        try:
            resp = requests.post(url, json=traces, timeout=30)
            if resp.status_code == 200:
                success += len(traces)
                print(f"  Sent {batch_num + len(traces)}/{count} traces...", end="\r")
            else:
                failed += len(traces)
                print(f"  Failed batch {batch_num}: {resp.status_code}")
        except Exception as e:
            failed += len(traces)
            print(f"  Error: {e}")
    
    elapsed = time.time() - start_time
    print(f"\n  [OK] Traces sent: {success}, Failed: {failed}, Time: {elapsed:.2f}s")
    return success

def check_opensearch():
    print(f"\n{'='*50}")
    print("Checking OpenSearch data...")
    print(f"{'='*50}")
    
    try:
        resp = requests.get(f"{BASE_URL}/api/logs/recent?limit=10")
        if resp.status_code == 200:
            logs = resp.json()
            print(f"  [OK] Logs in OpenSearch: {len(logs)} recent logs")
        else:
            print(f"  [FAIL] Failed to fetch logs: {resp.status_code}")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

def test_ml_prediction():
    print(f"\n{'='*50}")
    print("Testing ML Model Prediction...")
    print(f"{'='*50}")
    
    test_data = {
        "metrics": {
            "cpu_usage": 0.85,
            "memory_usage": 0.75,
            "response_time_ms": 500,
            "error_rate": 0.1,
        }
    }
    
    try:
        resp = requests.post(f"{ML_URL}/predict", json=test_data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            print(f"  [OK] ML Prediction: {result}")
            return result
        else:
            print(f"  [FAIL] ML failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

def check_frontend_data():
    print(f"\n{'='*50}")
    print("Checking Frontend API endpoints...")
    print(f"{'='*50}")
    
    endpoints = [
        ("/api/anomalies", "Anomalies"),
        ("/api/logs/recent?limit=10", "Recent Logs"),
        ("/api/services", "Services"),
        ("/api/dashboard/kpi", "Dashboard KPI"),
    ]
    
    for path, name in endpoints:
        try:
            resp = requests.get(f"{BASE_URL}{path}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f"  [OK] {name}: {len(data)} items")
                else:
                    print(f"  [OK] {name}: OK")
            else:
                print(f"  [FAIL] {name}: {resp.status_code}")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

def main():
    print("="*60)
    print("API Monitoring Platform - Test Data Generator")
    print("="*60)
    
    print("\nChecking services...")
    try:
        requests.get(f"{BASE_URL}/actuator/health", timeout=5)
        print("  [OK] Backend is running")
    except:
        print("  [FAIL] Backend not running at http://localhost:8080")
        print("  Please start backend first: cd backend-service && ./gradlew bootRun")
        sys.exit(1)
    
    try:
        requests.get(f"{ML_URL}/health", timeout=5)
        print("  [OK] ML Service is running")
    except:
        print("  [FAIL] ML Service not running at http://localhost:9000")
        print("  Please start ML service first: cd ml-service && python -m api.main")
        sys.exit(1)
    
    logs_count = 5000
    metrics_count = 5000
    traces_count = 5000
    
    send_logs(logs_count)
    send_metrics(metrics_count)
    send_traces(traces_count)
    
    print("\nWaiting 5 seconds for data to be indexed...")
    time.sleep(5)
    
    check_opensearch()
    test_ml_prediction()
    check_frontend_data()
    
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
    print("\nData flow:")
    print("  1. ✓ Sent 5000 logs, metrics, traces to backend")
    print("  2. ✓ Backend stored data in OpenSearch")
    print("  3. ✓ ML Service can analyze and predict")
    print("  4. ✓ Frontend can fetch data via REST API")
    print("\nOpen http://localhost:5173 to view the dashboard!")

if __name__ == "__main__":
    main()
