#!/usr/bin/env python3
"""
Data Generator - Sends sample metrics, logs, and traces to the backend API
to populate the database so the Overview page shows data.
"""

import requests
import random
import time
import json
from datetime import datetime, timedelta
import sys

BACKEND_URL = "http://localhost:8080"

SERVICES = ["user-service", "payment-service", "order-service", "product-service", "notification-service"]
ENDPOINTS = ["/api/users", "/api/users/1", "/api/payments", "/api/orders", "/api/products", "/api/notifications"]
METHODS = ["GET", "POST", "PUT", "DELETE"]
ENVIRONMENTS = ["production", "staging", "development"]
LOG_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG"]

def generate_metric(service_name, endpoint, env):
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))
    cpu = round(random.uniform(10, 95), 2)
    memory = round(random.uniform(20, 90), 2)
    response_time = random.randint(10, 3000)
    error_rate = round(random.uniform(0, 20), 2)
    request_count = random.randint(10, 1000)
    
    return {
        "serviceName": service_name,
        "endpoint": endpoint,
        "environment": env,
        "cpuUsagePercent": cpu,
        "memoryUsagePercent": memory,
        "responseTimeMs": response_time,
        "errorRate": error_rate,
        "requestCount": request_count,
        "timestamp": timestamp.isoformat()
    }

def generate_log(service_name, endpoint, env, status_code):
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))
    log_level = "INFO"
    if status_code >= 500:
        log_level = "ERROR"
    elif status_code >= 400:
        log_level = "WARN"
    
    messages = {
        "INFO": ["Request processed successfully", "Operation completed", "Transaction committed"],
        "WARN": ["High latency detected", "Rate limit approaching", "Cache miss"],
        "ERROR": ["Connection timeout", "Database deadlock", "Service unavailable"]
    }
    
    return {
        "serviceName": service_name,
        "endpoint": endpoint,
        "environment": env,
        "method": random.choice(METHODS),
        "statusCode": status_code,
        "responseTimeMs": random.randint(10, 3000),
        "timestamp": timestamp.isoformat(),
        "logLevel": log_level,
        "message": random.choice(messages[log_level]),
        "traceId": f"trace-{random.randint(100000, 999999)}",
        "spanId": f"span-{random.randint(1000, 9999)}"
    }

def generate_trace(service_name, env):
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))
    status_code = random.choices([200, 201, 400, 404, 500], weights=[70, 10, 10, 5, 5])[0]
    duration = random.randint(10, 3000)
    
    return {
        "serviceName": service_name,
        "environment": env,
        "operationName": random.choice(ENDPOINTS),
        "traceId": f"trace-{random.randint(100000, 999999)}",
        "spanId": f"span-{random.randint(1000, 9999)}",
        "parentSpanId": f"span-{random.randint(100, 999)}",
        "startTime": timestamp.isoformat(),
        "duration": duration,
        "statusCode": status_code,
        "isError": status_code >= 400
    }

def send_metrics(n=50):
    """Send metrics to backend"""
    print(f"[METRICS] Sending {n} metrics to backend...")
    success = 0
    for i in range(n):
        service = random.choice(SERVICES)
        endpoint = random.choice(ENDPOINTS)
        env = random.choice(ENVIRONMENTS)
        
        metric = generate_metric(service, endpoint, env)
        try:
            # Try the direct endpoint first
            resp = requests.post(f"{BACKEND_URL}/api/metrics", json=metric, timeout=5)
            if resp.status_code in [200, 201, 202]:
                success += 1
            else:
                # Try alternative endpoint
                resp = requests.post(f"{BACKEND_URL}/api/metrics/api/metrics", json=metric, timeout=5)
                if resp.status_code in [200, 201, 202]:
                    success += 1
        except Exception as e:
            pass
        
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{n}")
    
    print(f"  [OK] Metrics sent: {success}/{n}")
    return success

def send_logs(n=50):
    """Send logs to backend"""
    print(f"[LOGS] Sending {n} logs to backend...")
    success = 0
    for i in range(n):
        service = random.choice(SERVICES)
        endpoint = random.choice(ENDPOINTS)
        env = random.choice(ENVIRONMENTS)
        status_code = random.choices([200, 201, 400, 404, 500], weights=[70, 10, 10, 5, 5])[0]
        
        log_entry = generate_log(service, endpoint, env, status_code)
        try:
            resp = requests.post(f"{BACKEND_URL}/api/logs/batch/raw", json=[log_entry], timeout=5)
            if resp.status_code in [200, 201, 202]:
                success += 1
        except Exception as e:
            pass
        
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{n}")
    
    print(f"  [OK] Logs sent: {success}/{n}")
    return success

def send_traces(n=50):
    """Send traces to backend"""
    print(f"[TRACES] Sending {n} traces to backend...")
    success = 0
    for i in range(n):
        service = random.choice(SERVICES)
        env = random.choice(ENVIRONMENTS)
        
        trace = generate_trace(service, env)
        try:
            resp = requests.post(f"{BACKEND_URL}/api/traces/ingest", json=trace, timeout=5)
            if resp.status_code in [200, 201, 202]:
                success += 1
        except Exception as e:
            pass
        
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{n}")
    
    print(f"  [OK] Traces sent: {success}/{n}")
    return success

def main():
    print("=" * 60)
    print("Data Generator - Populate Backend with Sample Data")
    print("=" * 60)
    
    # Check if backend is running
    try:
        resp = requests.get(f"{BACKEND_URL}/actuator/health", timeout=5)
        if resp.status_code != 200:
            print("ERROR: Backend is not responding properly")
            sys.exit(1)
        print("OK: Backend is running")
    except Exception as e:
        print(f"ERROR: Cannot connect to backend at {BACKEND_URL}")
        print("   Make sure backend is running: ./gradlew bootRun")
        sys.exit(1)
    
    # Generate data
    print("\nGenerating sample data...\n")
    
    metrics_sent = send_metrics(50)
    logs_sent = send_logs(50)
    traces_sent = send_traces(50)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Metrics: {metrics_sent}")
    print(f"  Logs:    {logs_sent}")
    print(f"  Traces:  {traces_sent}")
    print("=" * 60)
    print("\nOK: Data generation complete!")
    print("   Refresh the Overview page to see the data.")
    
if __name__ == "__main__":
    main()