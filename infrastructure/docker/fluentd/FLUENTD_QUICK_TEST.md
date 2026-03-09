# Quick Fluentd Testing Commands

Use these commands to quickly send a log to Fluentd and verify it appears in OpenSearch.

## Option 1: Use the quick test scripts

```bash
cd infrastructure/docker

# Simple send-and-find (just 2 sec wait)
./send_and_find.sh

# Detailed verification with all components
./check_fluentd.sh
./check_fluentd.sh --force-flush  # Forces Fluentd restart for immediate indexing
```

## Option 2: Copy-paste one-liners

**Send a test log:**
```bash
curl -X POST http://localhost:9880/app.test \
  -H "Content-Type: application/json" \
  -d '{"message": "my test log", "level": "INFO"}'
```

**Wait and search for it:**
```bash
sleep 2 && curl -s "http://localhost:9200/logs-*/_search?pretty&size=5" \
  -H "Content-Type: application/json" \
  -d '{"query":{"match":{"message":"my test log"}}}'
```

**Or all at once:**
```bash
TEST_MSG="test-$(date +%s%N|tail -c 6)" && \
curl -s -X POST http://localhost:9880/app.test -H "Content-Type: application/json" -d "{\"message\":\"$TEST_MSG\"}" && \
echo "Sent: $TEST_MSG" && sleep 2 && \
curl -s "http://localhost:9200/logs-*/_count?pretty" -H "Content-Type: application/json" -d '{"query":{"match":{"message":"'$TEST_MSG'"}}}'
```

## Option 3: Separate steps (manual verification)

**1. Send:**
```bash
curl -X POST http://localhost:9880/app.test \
  -H "Content-Type: application/json" \
  -d '{"message": "test123", "level": "INFO"}'
```

**2. Check Fluentd buffer:**
```bash
docker exec fluentd ls -lh /fluentd/log/opensearch.buffer/
docker compose logs fluentd --tail 5
```

**3. Check OpenSearch health:**
```bash
curl http://localhost:9200/_cluster/health?pretty
```

**4. Search for log:**
```bash
curl "http://localhost:9200/logs-*/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{"query":{"match":{"message":"test123"}}}'
```

**5. Count all logs:**
```bash
curl "http://localhost:9200/logs-*/_count?pretty"
```

## Option 4: Tag-based logs (app vs system)

**Send application log:**
```bash
curl -X POST http://localhost:9880/app.backend \
  -H "Content-Type: application/json" \
  -d '{"message": "API call succeeded", "endpoint": "/users"}'
```

**Send system log:**
```bash
curl -X POST http://localhost:9880/system.monitor \
  -H "Content-Type: application/json" \
  -d '{"message": "Disk check passed", "usage": 45}'
```

**Search by tag:**
```bash
curl "http://localhost:9200/logs-*/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{"query":{"term":{"@log_tag":"app.backend"}}}'
```

## Troubleshooting

**Logs not appearing immediately?**
- Normal behavior due to `timekey 3600` (hourly batching)
- Run: `./check_fluentd.sh --force-flush` to restart Fluentd and flush all buffered logs
- Or restart manually: `docker compose restart fluentd`

**OpenSearch not responding?**
```bash
curl http://localhost:9200/_cluster/health?pretty
docker compose ps opensearch
```

**Fluentd not healthy?**
```bash
./check_fluentd.sh
docker logs fluentd --tail 30
```

## Common Workflows

### Workflow 1: Quick verify everything is working (30 seconds)
```bash
./quick_test.sh
```

### Workflow 2: Comprehensive health check
```bash
./check_fluentd.sh
```

### Workflow 3: Verify and force immediate indexing
```bash
./check_fluentd.sh --force-flush
```

### Workflow 4: Manual step-by-step
```bash
# 1. Send
MSG="test-$(date +%s)" && curl -X POST http://localhost:9880/app.test \
  -H "Content-Type: application/json" -d "{\"message\":\"$MSG\"}"

# 2. Wait
sleep 2

# 3. Find
curl "http://localhost:9200/logs-*/_count" -H "Content-Type: application/json" \
  -d '{"query":{"match":{"message":"'$MSG'"}}}'
```
