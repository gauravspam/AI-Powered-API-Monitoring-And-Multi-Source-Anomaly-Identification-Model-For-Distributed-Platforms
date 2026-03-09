# Fluentd Dockerfile for Log Collection
# Purpose: Collect application logs and ship them to OpenSearch
# Architecture: Option B - Fluentd for logs only, backend APIs for metrics/traces

FROM fluent/fluentd:v1.17-1

# Switch to root for plugin installation
USER root

# Install required plugins
RUN fluent-gem install fluent-plugin-opensearch \
    && fluent-gem install fluent-plugin-record-modifier \
    && fluent-gem install fluent-plugin-rewrite-tag-filter \
    && fluent-gem install fluent-plugin-concat \
    && fluent-gem install fluent-plugin-prometheus

# Create buffer directory with proper permissions
RUN mkdir -p /fluentd/log /fluentd/etc /fluentd/plugins \
    && chown -R fluent:fluent /fluentd

# Switch back to fluent user
USER fluent

# Configuration will be mounted as volume
# Default config location: /fluentd/etc/fluent.conf

EXPOSE 24224 24224/udp 9880

CMD ["fluentd", "-c", "/fluentd/etc/fluent.conf"]
