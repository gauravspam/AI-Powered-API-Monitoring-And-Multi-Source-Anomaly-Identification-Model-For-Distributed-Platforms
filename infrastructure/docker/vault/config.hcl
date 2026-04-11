# Vault Configuration for Production Mode
# For development, we use dev mode. For production, use this config.

# listener "tcp" {
#   tls_disable = 1
#   address = "[::]:8200"
#   cluster_address = "[::]:8201"
# }

# storage "raft" {
#   path = "/vault/data"
#   retry_join {
#     leader_api_addr = "http://vault:8200"
#   }
# }

# disable_mlock = true
# ui = true
# service_registration "kubernetes" {}

# For demonstration, we'll use the file backend
storage "file" {
  path = "/vault/data"
}

# This is for development/demo only
# In production, use backend storage like Consul or PostgreSQL

listener "tcp" {
  tls_disable = "true"
  address = "0.0.0.0:8200"
}

elemetry {
  prometheus_retention_time = "30s"
  disable_hostname = "true"
}

ui = true

# Log level
log_level = "INFO"

# Default lease duration
default_lease_ttl = "3600"
max_lease_ttl = "86400"