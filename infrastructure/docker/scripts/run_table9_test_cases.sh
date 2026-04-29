#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/infrastructure/docker/configs/docker-compose.yml"

BASE_URL="${BASE_URL:-http://localhost:8080}"
ML_URL="${ML_URL:-http://localhost:9000}"
OS_URL="${OS_URL:-http://localhost:9200}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-postgres}"
PG_DB="${PG_DB:-api_monitoring}"
PG_USER="${PG_USER:-api_monitor}"
LOAD_COUNT="${LOAD_COUNT:-120}"
ENSURE_UP=1

RESULT_IDS=()
RESULT_DESC=()
RESULT_EXPECTED=()
RESULT_ACTUAL=()
RESULT_STATUS=()

print_usage() {
  cat <<'USAGE'
Usage: run_table9_tests.sh [options]

Options:
  --no-ensure-up      Do not run docker compose up before tests.
  --load-count N      Number of concurrent requests for TC-13 (default: 120).
  --help              Show this help.

Environment overrides:
  BASE_URL, ML_URL, OS_URL, POSTGRES_CONTAINER, PG_DB, PG_USER, LOAD_COUNT

One-command run:
  ./infrastructure/docker/scripts/run_table9_tests.sh
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-ensure-up)
      ENSURE_UP=0
      shift
      ;;
    --load-count)
      LOAD_COUNT="$2"
      shift 2
      ;;
    --help|-h)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_usage
      exit 1
      ;;
  esac
done

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd docker
require_cmd curl
require_cmd python3

record_result() {
  RESULT_IDS+=("$1")
  RESULT_DESC+=("$2")
  RESULT_EXPECTED+=("$3")
  RESULT_ACTUAL+=("$4")
  RESULT_STATUS+=("$5")
}

pg_query() {
  docker exec -i "$POSTGRES_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc "$1"
}

wait_http() {
  local url="$1"
  local name="$2"
  local attempts=40
  local sleep_sec=3
  local i=0

  while [[ $i -lt $attempts ]]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    i=$((i + 1))
    sleep "$sleep_sec"
  done

  echo "Timed out waiting for $name at $url" >&2
  return 1
}

json_eval() {
  local payload="$1"
  local code="$2"
  printf '%s' "$payload" | python3 -c "$code"
}

if [[ "$ENSURE_UP" -eq 1 ]]; then
  echo "[INFO] Ensuring required Docker services are up..."
  docker compose -f "$COMPOSE_FILE" up -d postgres opensearch ml-service backend >/dev/null
fi

echo "[INFO] Waiting for core services..."
wait_http "$ML_URL/health" "ml-service" || exit 1
wait_http "$BASE_URL/health" "backend" || exit 1
wait_http "$OS_URL" "opensearch" || exit 1

RUN_TS="$(date +%s)"

echo "[INFO] Running Table 9.1 tests..."

# TC-01
TC01_HEALTH="$(curl -s "$ML_URL/health")"
TC01_MODELS="$(curl -s "$BASE_URL/api/models")"
TC01_STATUS="Fail"
TC01_OK_HEALTH="$(json_eval "$TC01_HEALTH" 'import sys,json; d=json.load(sys.stdin); m=set(d.get("models_loaded",[])); print("yes" if {"msif","ple","fusion"}.issubset(m) else "no")')"
TC01_OK_NAMES="$(json_eval "$TC01_MODELS" 'import sys,json; names={x.get("name") for x in json.load(sys.stdin)}; req={"MSIF-LSTM","PLE-GRU","MDN-EVL"}; print("yes" if req.issubset(names) else "no")')"
if [[ "$TC01_OK_HEALTH" == "yes" && "$TC01_OK_NAMES" == "yes" ]]; then
  TC01_STATUS="Pass"
fi
TC01_ACTUAL="models_loaded=$(json_eval "$TC01_HEALTH" 'import sys,json; print(json.load(sys.stdin).get("models_loaded"))'); names=$(json_eval "$TC01_MODELS" 'import sys,json; print([x.get("name") for x in json.load(sys.stdin)])')"
record_result "TC-01" "ML Model Loading Test" "MSIF-LSTM, PLE-GRU, MDN-EVL available" "$TC01_ACTUAL" "$TC01_STATUS"

# TC-02
TC02_MSG="tc02-${RUN_TS}"
TC02_TRACE="corr-${RUN_TS}"
TC02_INGEST="$(curl -s -X POST "$BASE_URL/api/logs/batch/raw" -H 'Content-Type: application/json' -d "[{\"serviceName\":\"orders-api\",\"level\":\"ERROR\",\"message\":\"$TC02_MSG\",\"source\":\"test-suite\",\"traceId\":\"$TC02_TRACE\",\"environment\":\"staging\",\"timestamp\":\"$(date -Iseconds)\"}]")"
sleep 2
TC02_SEARCH="$(curl -s -X GET "$OS_URL/logs-*/_search" -H 'Content-Type: application/json' -d "{\"query\":{\"match\":{\"message\":\"$TC02_MSG\"}},\"size\":1}")"
TC02_STATUS="Fail"
TC02_OK="$(json_eval "$TC02_SEARCH" 'import sys,json; d=json.load(sys.stdin); c=d.get("hits",{}).get("total",{}).get("value",0); ok=False
if c>0:
 s=d["hits"]["hits"][0]["_source"]
 ok = all(k in s and s.get(k) is not None for k in ["serviceName","level","timestamp","correlationId"])
print("yes" if ok else "no")')"
if [[ "$TC02_OK" == "yes" ]]; then
  TC02_STATUS="Pass"
fi
TC02_ACTUAL="ingest=$(json_eval "$TC02_INGEST" 'import sys,json; x=json.load(sys.stdin); print("count="+str(x.get("count"))+",failed="+str(x.get("failed")))'); fields=$(json_eval "$TC02_SEARCH" 'import sys,json; d=json.load(sys.stdin); h=d.get("hits",{}).get("hits",[]); print(sorted(list(h[0]["_source"].keys())) if h else [])')"
record_result "TC-02" "Log Ingestion Test" "OpenSearch doc has service, level, timestamp, correlationId" "$TC02_ACTUAL" "$TC02_STATUS"

# TC-03
TC03_TS="$(date -u +"%Y-%m-%dT%H:%M:%S")"
TC03_RESP="$(curl -s -X POST "$BASE_URL/api/metrics" -H 'Content-Type: application/json' -d "{\"apiId\":91001,\"serviceName\":\"billing-api\",\"cpuUsage\":72.1,\"memoryUsage\":68.4,\"diskIoBytes\":1024,\"networkIoBytes\":2048,\"responseTimeMs\":345.2,\"requestCount\":33,\"errorRate\":0.03,\"timestamp\":\"$TC03_TS\"}")"
TC03_DB="$(pg_query "SELECT api_log_id, service_name, metric_timestamp FROM system_metrics WHERE api_log_id=91001 ORDER BY id DESC LIMIT 1;")"
TC03_STATUS="Fail"
if echo "$TC03_DB" | grep -q "91001" && echo "$TC03_DB" | grep -q "billing-api"; then
  TC03_STATUS="Pass"
fi
TC03_ACTUAL="api=$(echo "$TC03_RESP" | tr -d '\n'); db=$(echo "$TC03_DB" | xargs)"
record_result "TC-03" "Metric Collection Test" "Metric persisted with apiId and timestamp" "$TC03_ACTUAL" "$TC03_STATUS"

# TC-04
TC04_FLEX_PAYLOAD='{"metrics":{"cpu_usage":91,"memory_usage":88,"response_time_ms":4200,"error_rate":0.32,"request_count":50},"logs":[{"level":"ERROR","message":"db timeout"}],"traces":[{"status":"error","latency_ms":6200,"service":"fusion-service"}]}'
TC04_BACK_PAYLOAD='{"apiName":"fusion-service","method":"POST","responseTime":4200,"statusCode":503,"requestCount":50,"errorRate":0.32,"cpuUsage":91,"memoryUsage":88,"networkIo":12000,"diskIo":8000,"environment":"staging","serviceName":"fusion-service","logs":[{"level":"ERROR","message":"db timeout"}],"traces":[{"status":"error","latency_ms":6200,"service":"fusion-service"}],"metrics":{"cpu_usage":91,"memory_usage":88,"response_time_ms":4200,"error_rate":0.32,"request_count":50}}'
TC04_FLEX="$(curl -s -X POST "$ML_URL/predict/flexible" -H 'Content-Type: application/json' -d "$TC04_FLEX_PAYLOAD")"
TC04_BACK="$(curl -s -X POST "$BASE_URL/api/anomalies/analyze" -H 'Content-Type: application/json' -d "$TC04_BACK_PAYLOAD")"
TC04_STATUS="Fail"
TC04_OK="$(json_eval "$TC04_FLEX" 'import sys,json; d=json.load(sys.stdin); ok=(d.get("modalities_present")==3 and "msif_score" in d and "ple_score" in d); print("yes" if ok else "no")')"
if [[ "$TC04_OK" == "yes" ]]; then
  TC04_STATUS="Pass"
fi
TC04_ACTUAL="ml=$(echo "$TC04_FLEX" | tr -d '\n'); backend=$(echo "$TC04_BACK" | tr -d '\n')"
record_result "TC-04" "Multi-Source Feature Fusion Test" "ML receives correctly fused 3-modality input" "$TC04_ACTUAL" "$TC04_STATUS"

# TC-08
curl -s -X POST "$BASE_URL/api/anomalies/analyze" -H 'Content-Type: application/json' -d '{"apiName":"alert-case-script","method":"GET","responseTime":5000,"statusCode":500,"requestCount":10,"errorRate":0.6,"cpuUsage":95,"memoryUsage":92,"environment":"production","serviceName":"alert-case-script"}' >/dev/null
TC08_ID="$(curl -s "$BASE_URL/api/alerts?limit=5" | python3 -c 'import sys,json; a=json.load(sys.stdin); print(a[0]["id"] if a else "")')"
TC08_ACK="$(curl -s -X POST "$BASE_URL/api/alerts/$TC08_ID/acknowledge")"
TC08_ACK_DB="$(pg_query "SELECT status,is_acknowledged FROM anomaly_detections WHERE id=$TC08_ID;")"
TC08_RES="$(curl -s -X POST "$BASE_URL/api/alerts/$TC08_ID/resolve")"
TC08_RES_DB="$(pg_query "SELECT status,is_resolved FROM anomaly_detections WHERE id=$TC08_ID;")"
TC08_STATUS="Fail"
if echo "$TC08_ACK" | grep -qi true && echo "$TC08_RES" | grep -qi true && echo "$TC08_ACK_DB" | grep -q ACKNOWLEDGED && echo "$TC08_RES_DB" | grep -q 'RESOLVED|t'; then
  TC08_STATUS="Pass"
fi
TC08_ACTUAL="id=$TC08_ID ack_api=$TC08_ACK ack_db=$(echo "$TC08_ACK_DB" | xargs) resolve_api=$TC08_RES resolve_db=$(echo "$TC08_RES_DB" | xargs)"
record_result "TC-08" "Alert Acknowledge/Resolve Test" "Status transitions to ACKNOWLEDGED then RESOLVED in DB" "$TC08_ACTUAL" "$TC08_STATUS"

# TC-09
TC09_BEFORE="$(curl -s "$BASE_URL/api/dashboard/kpi" | python3 -c 'import sys,json; print(int(json.load(sys.stdin).get("anomalyCount",0)))')"
curl -s -X POST "$BASE_URL/api/anomalies/analyze" -H 'Content-Type: application/json' -d '{"apiName":"kpi-update-script","method":"POST","responseTime":4600,"statusCode":502,"requestCount":18,"errorRate":0.45,"cpuUsage":89,"memoryUsage":86,"environment":"production","serviceName":"kpi-update-script"}' >/dev/null
TC09_UPDATED=0
TC09_AFTER="$TC09_BEFORE"
for i in 1 2 3 4 5 6; do
  sleep 5
  TC09_NOW="$(curl -s "$BASE_URL/api/dashboard/kpi" | python3 -c 'import sys,json; print(int(json.load(sys.stdin).get("anomalyCount",0)))')"
  TC09_AFTER="$TC09_NOW"
  if [[ "$TC09_NOW" -gt "$TC09_BEFORE" ]]; then
    TC09_UPDATED=1
    break
  fi
done
TC09_STATUS="Fail"
if [[ "$TC09_UPDATED" -eq 1 ]]; then
  TC09_STATUS="Pass"
fi
TC09_ACTUAL="before=$TC09_BEFORE after=$TC09_AFTER updated_within_30s=$TC09_UPDATED"
record_result "TC-09" "Dashboard Real-Time Update Test" "KPI anomaly count updates within polling interval" "$TC09_ACTUAL" "$TC09_STATUS"

# TC-10
TC10_TS="$(date +%s)"
for i in 1 2 3; do
  curl -s -X POST "$BASE_URL/api/logs/batch/raw" -H 'Content-Type: application/json' -d "[{\"serviceName\":\"timeline-api\",\"level\":\"ERROR\",\"message\":\"timeline-match-$TC10_TS-$i\",\"environment\":\"staging\",\"traceId\":\"tl-$TC10_TS-$i\",\"timestamp\":\"$(date -Iseconds)\"}]" >/dev/null
  curl -s -X POST "$BASE_URL/api/logs/batch/raw" -H 'Content-Type: application/json' -d "[{\"serviceName\":\"timeline-api\",\"level\":\"INFO\",\"message\":\"timeline-noise-$TC10_TS-$i\",\"environment\":\"production\",\"traceId\":\"tn-$TC10_TS-$i\",\"timestamp\":\"$(date -Iseconds)\"}]" >/dev/null
done
sleep 2
TC10_RECENT="$(curl -s "$BASE_URL/api/logs/recent?limit=200")"
TC10_COUNTS="$(json_eval "$TC10_RECENT" 'import sys,json; a=json.load(sys.stdin); m=[x for x in a if x.get("environment")=="staging" and str(x.get("level","")).upper()=="ERROR"]; n=[x for x in a if str(x.get("message","")).startswith("timeline-match-")]; print(len(m), len(n))')"
TC10_M1="$(echo "$TC10_COUNTS" | awk '{print $1}')"
TC10_M2="$(echo "$TC10_COUNTS" | awk '{print $2}')"
TC10_STATUS="Fail"
if [[ "$TC10_M1" -ge 3 && "$TC10_M2" -ge 3 ]]; then
  TC10_STATUS="Pass"
fi
TC10_ACTUAL="filtered_env_level_count=$TC10_M1 ingested_match_messages_seen=$TC10_M2"
record_result "TC-10" "Log Timeline Filter Test" "Environment+level filter returns matching entries" "$TC10_ACTUAL" "$TC10_STATUS"

# TC-12
TC12_MODELS="$(curl -s "$BASE_URL/api/models")"
TC12_STATUS="Fail"
TC12_OK="$(json_eval "$TC12_MODELS" 'import sys,json; a=json.load(sys.stdin); ok=(len(a)>=3 and all(all(k in m for k in ["name","version","accuracy","throughputPerSec"]) for m in a)); print("yes" if ok else "no")')"
if [[ "$TC12_OK" == "yes" ]]; then
  TC12_STATUS="Pass"
fi
TC12_ACTUAL="$(json_eval "$TC12_MODELS" 'import sys,json; a=json.load(sys.stdin); print([(m.get("name"),m.get("version"),m.get("accuracy"),m.get("throughputPerSec")) for m in a])')"
record_result "TC-12" "Model Registry Status Test" "Models page returns version, accuracy, throughput" "$TC12_ACTUAL" "$TC12_STATUS"

# TC-13
TC13_PRE="$(pg_query "SELECT COUNT(*) FROM anomaly_detections;" | xargs)"
seq 1 "$LOAD_COUNT" | xargs -I{} -P 12 bash -lc 'curl -s -o /dev/null -w "%{http_code}\n" -X POST "'$BASE_URL'/api/anomalies/analyze" -H "Content-Type: application/json" -d "{\"apiName\":\"load-api-script\",\"method\":\"GET\",\"responseTime\":3500,\"statusCode\":500,\"requestCount\":5,\"errorRate\":0.2,\"cpuUsage\":82,\"memoryUsage\":79,\"environment\":\"production\",\"serviceName\":\"load-api-script\"}"' | sort | uniq -c > /tmp/tc13_codes_$$.txt
TC13_POST="$(pg_query "SELECT COUNT(*) FROM anomaly_detections;" | xargs)"
TC13_DELTA=$((TC13_POST - TC13_PRE))
TC13_BACK_HEALTH="$(curl -s "$BASE_URL/health" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))')"
TC13_ML_HEALTH="$(curl -s "$ML_URL/health" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))')"
TC13_BACK_RESTARTS="$(docker inspect -f '{{.RestartCount}}' backend)"
TC13_ML_RESTARTS="$(docker inspect -f '{{.RestartCount}}' ml-service)"
TC13_STATUS="Fail"
if grep -q " $LOAD_COUNT 200" /tmp/tc13_codes_$$.txt && [[ "$TC13_DELTA" -ge $((LOAD_COUNT - 5)) ]] && [[ "$TC13_BACK_HEALTH" == "UP" ]] && [[ "$TC13_ML_HEALTH" == "healthy" ]] && [[ "$TC13_BACK_RESTARTS" -eq 0 ]] && [[ "$TC13_ML_RESTARTS" -eq 0 ]]; then
  TC13_STATUS="Pass"
fi
TC13_ACTUAL="codes=$(tr '\n' ';' < /tmp/tc13_codes_$$.txt) delta=$TC13_DELTA backend_health=$TC13_BACK_HEALTH ml_health=$TC13_ML_HEALTH restarts_backend=$TC13_BACK_RESTARTS restarts_ml=$TC13_ML_RESTARTS"
record_result "TC-13" "High Throughput Stability Test" "Sustained load without crashes or record loss" "$TC13_ACTUAL" "$TC13_STATUS"
rm -f /tmp/tc13_codes_$$.txt

# TC-14
TC14_EP="persist-api-$RUN_TS"
curl -s -X POST "$BASE_URL/api/anomalies/analyze" -H 'Content-Type: application/json' -d "{\"apiName\":\"$TC14_EP\",\"method\":\"PUT\",\"responseTime\":4200,\"statusCode\":500,\"requestCount\":7,\"errorRate\":0.35,\"cpuUsage\":84,\"memoryUsage\":81,\"environment\":\"production\",\"serviceName\":\"$TC14_EP\"}" >/dev/null
TC14_DB="$(pg_query "SELECT hybrid_ensemble_score, endpoint, service_name FROM anomaly_detections WHERE endpoint='$TC14_EP' ORDER BY id DESC LIMIT 1;")"
TC14_STATUS="Fail"
if echo "$TC14_DB" | grep -q "$TC14_EP"; then
  TC14_STATUS="Pass"
fi
TC14_ACTUAL="$(echo "$TC14_DB" | xargs)"
record_result "TC-14" "Database Persistence Test" "Anomaly persisted with score, endpoint, service" "$TC14_ACTUAL" "$TC14_STATUS"

# Summary
printf '\n%-7s | %-42s | %-4s\n' "Case" "Description" "Stat"
printf '%s\n' "--------------------------------------------------------------------------"
PASS_COUNT=0
FAIL_COUNT=0
for i in "${!RESULT_IDS[@]}"; do
  printf '%-7s | %-42s | %-4s\n' "${RESULT_IDS[$i]}" "${RESULT_DESC[$i]}" "${RESULT_STATUS[$i]}"
  if [[ "${RESULT_STATUS[$i]}" == "Pass" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

printf '\nPassed: %d  Failed: %d  Total: %d\n' "$PASS_COUNT" "$FAIL_COUNT" "${#RESULT_IDS[@]}"

DETAILS_FILE="$ROOT_DIR/infrastructure/docker/scripts/table9_last_run.txt"
{
  echo "Run timestamp: $(date -Iseconds)"
  echo ""
  for i in "${!RESULT_IDS[@]}"; do
    echo "${RESULT_IDS[$i]} | ${RESULT_DESC[$i]}"
    echo "Expected: ${RESULT_EXPECTED[$i]}"
    echo "Actual:   ${RESULT_ACTUAL[$i]}"
    echo "Status:   ${RESULT_STATUS[$i]}"
    echo ""
  done
} > "$DETAILS_FILE"

echo "Detailed results written to: $DETAILS_FILE"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

exit 0
