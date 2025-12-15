# GKE Cluster configuration for test environment

name_prefix = "ags-test"
environment = "test"
project_id  = "YOUR_PROJECT_ID"
region      = "us-central1"
zones       = ["us-central1-a"] # Limit to single zone for test environment

# Cluster configuration
release_channel        = "REGULAR"
deletion_protection    = false
enable_public_endpoint = true            # Public endpoint for test environment
master_cidr            = "172.16.1.0/28" # GKE master range

# Application configuration
docker_image     = "gcr.io/YOUR_PROJECT_ID/aerospike-graph-service:VERSION"
cpu_architecture = "arm64" # Options: amd64, arm64
replicas         = 2
cpu_request      = "500m"
memory_request   = "1Gi"
cpu_limit        = "1000m"
memory_limit     = "2Gi"

enable_external_lb = true

# Aerospike connection
env_vars = {
  "aerospike.client.namespace" = "test"
  "aerospike.client.host"      = "YOUR_AEROSPIKE_HOST:3000"
}

# Autoscaling configuration
enable_autoscaling = false
