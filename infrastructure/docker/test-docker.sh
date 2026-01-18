#!/bin/bash
set -e

echo "=== Docker Services Test ==="

echo "1. Checking containers..."
docker-compose ps

echo -e "\n2. Testing PostgreSQL..."
docker exec postgres psql -U api_monitor -d api_monitoring -c "SELECT version();" || echo "❌ PostgreSQL failed"

echo -e "\n3. Testing OpenSearch..."
curl -s http://localhost:9200 | jq .version.number || echo "❌ OpenSearch failed"

echo -e "\n4. Testing Backend Health..."
curl -s http://localhost:8081/actuator/health | jq .status || echo "❌ Backend failed"

echo -e "\n5. Testing Frontend..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "❌ Frontend failed"

echo -e "\n6. Checking Database Schema..."
docker exec postgres psql -U api_monitor -d api_monitoring -c "\dt" || echo "❌ Schema failed"

echo -e "\n7. Testing Backend Endpoints..."
curl -s http://localhost:8081/api/dashboard/anomalies?limit=1 | jq . || echo "❌ API failed"

echo -e "\n✅ All tests completed!"
