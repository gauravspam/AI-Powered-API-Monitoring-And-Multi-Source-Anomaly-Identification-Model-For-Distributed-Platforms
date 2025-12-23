# Fluentd Configuration

This directory contains the Fluentd aggregator configuration for the API Monitoring Platform.

## Structure

- `Dockerfile` - Custom Fluentd image with required plugins
- `conf/fluentd.conf` - Main Fluentd configuration file
- `logs/` - Directory for Fluentd logs (mounted as volume)

## Plugins Used

- `fluent-plugin-opensearch` - Output plugin for OpenSearch
- `fluent-plugin-postgres` - Output plugin for PostgreSQL

## Configuration

The Fluentd configuration (`fluentd.conf`) is mounted into the container at `/fluentd/etc/`.

### Input Sources

1. **Forward Protocol** (port 24224) - Receives logs from Fluent Bit agents
2. **HTTP Input** (port 9880) - Receives logs via HTTP POST requests

### Output Destinations

1. **OpenSearch** - Stores logs in OpenSearch indices with logstash format
2. **PostgreSQL** - Stores log metadata in PostgreSQL database

## Usage

Fluentd is automatically started with Docker Compose. To manually start:

```bash
cd infrastructure/docker
docker compose up fluentd
```

## Testing

Send a test log via HTTP:

```bash
curl -X POST http://localhost:9880/api-logs.test \
  -H "Content-Type: application/json" \
  -d '{
    "service": "test-service",
    "level": "INFO",
    "message": "Test log message",
    "timestamp": 1234567890
  }'
```

## Troubleshooting

- Check Fluentd logs: `docker logs fluentd`
- Verify buffer directory: `docker exec fluentd ls -la /var/log/fluentd-buffer`
- Test OpenSearch connection: `docker exec fluentd curl -k https://opensearch:9200 -u admin:Str0ng@ApiMon#2025`

