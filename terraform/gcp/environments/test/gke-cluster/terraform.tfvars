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

# Node Pool configuration (standard mode)
cluster_initial_node_count = 1                # Temporary default pool (will be removed)
node_pool_machine_type     = "n2d-standard-8"
node_pool_disk_size_gb  = 100
node_pool_disk_type     = "pd-standard"     # Options: pd-standard, pd-ssd
node_pool_min_count     = 1
node_pool_max_count     = 10
node_pool_initial_count = 1
node_pool_preemptible   = false             # Set to true for cost savings (can be terminated)
node_pool_spot          = false             # Set to true for even cheaper VMs (cannot use with preemptible)
node_pool_auto_repair   = true
node_pool_auto_upgrade  = true

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
