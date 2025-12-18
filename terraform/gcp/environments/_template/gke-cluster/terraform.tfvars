# GKE Cluster configuration
# TODO: Replace all TODO values before deployment

name_prefix = "ags-TODO_ENVIRONMENT" # TODO: Replace (e.g., 'ags-test', 'ags-prod')
environment = "TODO_ENVIRONMENT"     # TODO: Replace with environment name
project_id  = "TODO_PROJECT_ID"      # TODO: Replace with GCP project ID
region      = "us-central1"          # TODO: Adjust region if needed
zones       = []                     # Optional: limit to specific zones, e.g., ["us-central1-a", "us-central1-b"]

# Cluster configuration
release_channel        = "REGULAR"
deletion_protection    = false # TODO: Set to true for production
enable_public_endpoint = false # Set to true to allow public access to GKE control plane
master_cidr            = "172.16.1.0/28" # GKE master range

# Node Pool configuration (standard mode)
cluster_initial_node_count = 1                # Temporary default pool (will be removed)
node_pool_machine_type  = "e2-standard-4"      # Examples: e2-standard-4, n2-standard-4, t2a-standard-4 (ARM64)
node_pool_disk_size_gb  = 100                  # Disk size in GB
node_pool_disk_type     = "pd-standard"        # Options: pd-standard, pd-ssd
node_pool_min_count     = 1                    # Minimum nodes
node_pool_max_count     = 10                   # Maximum nodes
node_pool_initial_count = 2                    # Initial node count
node_pool_preemptible   = false                 # Use preemptible VMs (cheaper but can be terminated)
node_pool_spot          = false                 # Use spot VMs (cheaper than preemptible)
node_pool_auto_repair   = true                  # Auto-repair unhealthy nodes
node_pool_auto_upgrade  = true                  # Auto-upgrade node OS

# Application configuration
docker_image     = "gcr.io/TODO_PROJECT_ID/aerospike-graph-service:latest" # TODO: Update image
cpu_architecture = "arm64"                                                 # Options: amd64, arm64
replicas         = 2                                                       # TODO: Adjust for production
cpu_request      = "500m"
memory_request   = "1Gi"
cpu_limit        = "1000m"
memory_limit     = "2Gi"

enable_external_lb = true # Set to false for internal only

# Aerospike connection - TODO: Update with actual values
env_vars = {
  "aerospike.client.namespace" = "default"
  "aerospike.client.host"      = "TODO_AEROSPIKE_HOST:3000" # TODO: Aerospike cluster IP
  "aerospike.client.user"      = "TODO_USERNAME"            # TODO: Aerospike username
  "aerospike.client.password"  = "TODO_PASSWORD"            # TODO: Aerospike password
}

# Autoscaling configuration
enable_autoscaling    = false # TODO: Enable for production
min_replicas          = 2     # Minimum pods
max_replicas          = 10    # Maximum pods
cpu_target_percent    = 70    # Scale up when avg CPU > 70%
memory_target_percent = 80    # Scale up when avg memory > 80%

