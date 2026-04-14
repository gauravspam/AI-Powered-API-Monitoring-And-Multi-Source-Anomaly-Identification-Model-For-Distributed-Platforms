#!/usr/bin/env bash
# quick_test.sh - Send a test log to Fluentd and verify it in OpenSearch

set -u

TEST_ID="$(date +%s%N | tail -c 6)"
MESSAGE="quick-test-${TEST_ID}"

echo "📤 Sending test log to Fluentd (ID: $TEST_ID)..."
curl -s -X POST http://localhost:9880/app.test \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"$MESSAGE\",
    \"level\": \"INFO\",
    \"test_id\": \"$TEST_ID\",
    \"timestamp\": \"$(date -Iseconds)\"
  }" >/dev/null

echo "⏳ Waiting for Fluentd to process..."
sleep 2

echo "🔍 Searching OpenSearch for test log..."
RESULT=$(curl -s -X GET "http://localhost:9200/logs-*/_search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": {
      \"match\": {
        \"message\": \"$MESSAGE\"
      }
    },
    \"size\": 1,
    \"_source\": [\"message\", \"level\", \"test_id\", \"@timestamp\"]
  }" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = data['hits']['total']['value']
if count > 0:
    hit = data['hits']['hits'][0]['_source']
    print(f'✅ Found in OpenSearch!')
    print(f'   Message: {hit.get(\"message\")}')
    print(f'   Level: {hit.get(\"level\")}')
    print(f'   Timestamp: {hit.get(\"@timestamp\")}')
else:
    print('❌ Not found in OpenSearch (may be buffered, run with --force-flush)')
" 2>/dev/null || echo "❌ OpenSearch query failed")

echo "$RESULT"
echo
echo "📊 Recent logs (last 5):"
curl -s -X GET "http://localhost:9200/logs-*/_search?pretty&size=5" \
  -H "Content-Type: application/json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
hits = data['hits']['hits']
for i, hit in enumerate(hits, 1):
    src = hit['_source']
    ts = hit['_source'].get('@timestamp', 'N/A')
    msg = hit['_source'].get('message', 'N/A')[:60]
    print(f'{i}. [{ts}] {msg}')
" 2>/dev/null || echo "❌ Failed to fetch recent logs"
