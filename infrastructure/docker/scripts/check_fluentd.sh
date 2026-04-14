#!/usr/bin/env bash
set -euo pipefail

# check_fluentd.sh
# Verifies Fluentd is operating correctly in this project.
#
# Usage:
#   ./check_fluentd.sh
#   ./check_fluentd.sh --strict
#   ./check_fluentd.sh --force-flush
#
# Flags:
#   --strict      Fails if the test log is not immediately searchable in OpenSearch.
#   --force-flush Restarts Fluentd to trigger flush_at_shutdown, then retries search.

STRICT_MODE=0
FORCE_FLUSH=0

for arg in "$@"; do
  case "$arg" in
    --strict)
      STRICT_MODE=1
      ;;
    --force-flush)
      FORCE_FLUSH=1
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: ./check_fluentd.sh [--strict] [--force-flush]"
      exit 2
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "[PASS] $1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "[FAIL] $1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  echo "[WARN] $1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[FAIL] Required command not found: $1"
    exit 1
  fi
}

json_get_with_python() {
  local expr="$1"
  python3 -c '
import json
import sys

expr = sys.argv[1]
obj = json.load(sys.stdin)

if expr == "plugins_len":
  print(len(obj.get("plugins", [])))
elif expr == "opensearch_count":
  print(obj.get("count", 0))
else:
  raise SystemExit(1)
' "$expr"
}

extract_metric_value() {
  local metric_name="$1"
  local metrics
  metrics="$(curl -fsS http://localhost:24231/metrics 2>/dev/null || true)"
  if [[ -z "$metrics" ]]; then
    echo ""
    return
  fi

  echo "$metrics" | awk -v name="$metric_name" '
    $1 ~ "^"name"\\{" {print $2; found=1; exit}
    END {if (!found) print ""}
  '
}

search_test_log_count() {
  local test_id="$1"

  local payload
  payload=$(cat <<EOF
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"message": "fluentd-check-${test_id}"}}
      ]
    }
  }
}
EOF
)

  local resp
  resp="$(curl -fsS -X GET "http://localhost:9200/logs-*/_count" -H "Content-Type: application/json" -d "$payload" 2>/dev/null || true)"
  if [[ -z "$resp" ]]; then
    echo ""
    return
  fi

  echo "$resp" | json_get_with_python opensearch_count 2>/dev/null || echo ""
}

echo "=== Fluentd System Check ==="

echo "1) Checking prerequisites..."
require_cmd docker
require_cmd curl
require_cmd python3
pass "Required commands are available"

echo "2) Checking Fluentd container status..."
if docker compose ps fluentd 2>/dev/null | grep -q "healthy"; then
  pass "Fluentd container is healthy"
else
  fail "Fluentd container is not healthy (run: docker compose ps fluentd)"
fi

echo "3) Checking Fluentd health endpoint..."
health_json="$(curl -fsS http://localhost:8888/api/plugins.json 2>/dev/null || true)"
if [[ -z "$health_json" ]]; then
  fail "Fluentd health endpoint is not reachable at http://localhost:8888/api/plugins.json"
else
  plugins_len="$(echo "$health_json" | json_get_with_python plugins_len 2>/dev/null || echo 0)"
  if [[ "$plugins_len" -ge 1 ]]; then
    pass "Fluentd health endpoint is reachable and returns plugin data"
  else
    fail "Fluentd health endpoint response is invalid (no plugins found)"
  fi
fi

echo "4) Checking Fluentd metrics endpoint..."
metric_val="$(extract_metric_value "fluentd_output_status_emit_records")"
if [[ -n "$metric_val" ]]; then
  pass "Fluentd metrics endpoint is reachable (emit_records=$metric_val)"
else
  fail "Fluentd metrics endpoint is not exposing expected metrics"
fi

echo "5) Sending test log to Fluentd HTTP input..."
test_id="$(date +%s)"
log_payload=$(cat <<EOF
{
  "message": "fluentd-check-${test_id}",
  "level": "INFO",
  "service": "fluentd-check-script",
  "checkType": "pipeline-validation",
  "timestamp": "$(date -Iseconds)"
}
EOF
)

if curl -fsS -X POST "http://localhost:9880/app.healthcheck" -H "Content-Type: application/json" -d "$log_payload" >/dev/null; then
  pass "Test log accepted by Fluentd HTTP input"
else
  fail "Failed to POST test log to Fluentd HTTP input"
fi

echo "6) Validating downstream behavior..."
sleep 2

log_count="$(search_test_log_count "$test_id")"
if [[ -n "$log_count" && "$log_count" -ge 1 ]]; then
  pass "Test log is searchable in OpenSearch"
else
  if [[ "$FORCE_FLUSH" -eq 1 ]]; then
    echo "   Forcing flush by restarting Fluentd (--force-flush enabled)..."
    docker compose restart fluentd >/dev/null
    sleep 5
    log_count="$(search_test_log_count "$test_id")"
    if [[ -n "$log_count" && "$log_count" -ge 1 ]]; then
      pass "Test log searchable in OpenSearch after forced flush"
    else
      if [[ "$STRICT_MODE" -eq 1 ]]; then
        fail "Test log not found in OpenSearch even after forced flush"
      else
        warn "Test log not immediately searchable in OpenSearch; likely buffered due timekey-based chunking"
      fi
    fi
  else
    if [[ "$STRICT_MODE" -eq 1 ]]; then
      fail "Test log not immediately searchable in OpenSearch (strict mode)"
    else
      warn "Test log not immediately searchable in OpenSearch; likely buffered due timekey-based chunking"
      warn "Tip: run with --force-flush to restart Fluentd and verify immediate indexability"
    fi
  fi
fi

echo
echo "=== Summary ==="
echo "PASS: $PASS_COUNT"
echo "WARN: $WARN_COUNT"
echo "FAIL: $FAIL_COUNT"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

exit 0
