# Fluentd Dockerfile with OpenSearch and PostgreSQL plugins
FROM fluent/fluentd:v1.16-debian-1

USER root

# Install required plugins
RUN gem install fluent-plugin-opensearch --no-document
RUN gem install fluent-plugin-postgres --no-document

USER fluent

