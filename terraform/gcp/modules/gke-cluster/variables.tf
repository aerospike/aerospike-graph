# GKE Cluster Module Variables

variable "name_prefix" {
  type        = string
  description = "Prefix for all resource names (e.g., 'ags-test', 'ags-prod')"
}

variable "environment" {
  type        = string
  description = "Environment name (e.g., test, prod)"
}

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
}

variable "zones" {
  type        = list(string)
  description = "Specific zones for node placement. Leave empty to use all zones in region."
  default     = []
}

# Network configuration
variable "network_name" {
  type        = string
  description = "VPC network name"
}

variable "subnet_name" {
  type        = string
  description = "Subnet name for GKE nodes"
}

variable "pods_range_name" {
  type        = string
  description = "Secondary range name for pods"
}

variable "services_range_name" {
  type        = string
  description = "Secondary range name for services"
}

variable "master_cidr" {
  type        = string
  description = "CIDR range for GKE master"
  default     = "172.16.0.0/28"
}

# Cluster configuration
variable "release_channel" {
  type        = string
  description = "GKE release channel (RAPID, REGULAR, STABLE)"
  default     = "REGULAR"
}

variable "deletion_protection" {
  type        = bool
  description = "Enable deletion protection"
  default     = false
}

variable "enable_public_endpoint" {
  type        = bool
  description = "Enable public endpoint for GKE control plane (false = private cluster)"
  default     = false
}

variable "authorized_networks" {
  type = list(object({
    cidr = string
    name = string
  }))
  description = "List of authorized networks for master access"
  default = [{
    cidr = "0.0.0.0/0"
    name = "all"
  }]
}

# Application configuration
variable "app_namespace" {
  type        = string
  description = "Kubernetes namespace for the application"
  default     = "ags"
}

variable "cpu_architecture" {
  type        = string
  description = "CPU architecture for workloads (amd64 or arm64)"
  default     = "arm64"
  validation {
    condition     = contains(["amd64", "arm64"], var.cpu_architecture)
    error_message = "CPU architecture must be 'amd64' or 'arm64'."
  }
}

variable "docker_image" {
  type        = string
  description = "Docker image for Aerospike Graph Service"
}

variable "replicas" {
  type        = number
  description = "Number of replicas"
  default     = 2
}

variable "container_port" {
  type        = number
  description = "Container port for Gremlin"
  default     = 8182
}

variable "health_check_port" {
  type        = number
  description = "Health check port"
  default     = 9090
}

variable "health_check_path" {
  type        = string
  description = "Health check path"
  default     = "/healthcheck"
}

# Resource requests/limits
variable "cpu_request" {
  type        = string
  description = "CPU request"
  default     = "500m"
}

variable "cpu_limit" {
  type        = string
  description = "CPU limit"
  default     = "1000m"
}

variable "memory_request" {
  type        = string
  description = "Memory request"
  default     = "1Gi"
}

variable "memory_limit" {
  type        = string
  description = "Memory limit"
  default     = "2Gi"
}

# Environment variables
variable "env_vars" {
  type        = map(string)
  description = "Environment variables for the container"
  default     = {}
}

# Load balancer
variable "enable_external_lb" {
  type        = bool
  description = "Enable external load balancer (set false for internal only)"
  default     = true
}

# Autoscaling configuration
variable "enable_autoscaling" {
  type        = bool
  description = "Enable Horizontal Pod Autoscaler"
  default     = false
}

variable "min_replicas" {
  type        = number
  description = "Minimum number of replicas (HPA)"
  default     = 2
}

variable "max_replicas" {
  type        = number
  description = "Maximum number of replicas (HPA)"
  default     = 10
}

variable "cpu_target_percent" {
  type        = number
  description = "Target CPU utilization percentage for autoscaling"
  default     = 70
}

variable "memory_target_percent" {
  type        = number
  description = "Target memory utilization percentage for autoscaling"
  default     = 80
}

variable "scale_down_stabilization_seconds" {
  type        = number
  description = "Stabilization window for scale down (prevents flapping)"
  default     = 300
}

# Node pool configuration (for standard mode only)
variable "node_pool_machine_type" {
  type        = string
  description = "Machine type for node pool (standard mode only). Examples: e2-standard-4, n2-standard-4, t2a-standard-4 (ARM64)"
  default     = "e2-standard-4"
}

variable "node_pool_disk_size_gb" {
  type        = number
  description = "Disk size in GB for node pool (standard mode only)"
  default     = 100
}

variable "node_pool_disk_type" {
  type        = string
  description = "Disk type for node pool (standard mode only). Options: pd-standard, pd-ssd"
  default     = "pd-standard"
}

variable "node_pool_min_count" {
  type        = number
  description = "Minimum number of nodes in the node pool (standard mode only)"
  default     = 1
}

variable "node_pool_max_count" {
  type        = number
  description = "Maximum number of nodes in the node pool (standard mode only)"
  default     = 10
}

variable "cluster_initial_node_count" {
  type        = number
  description = "Initial node count for cluster default pool (will be removed, must be > 0)"
  default     = 1
}

variable "node_pool_initial_count" {
  type        = number
  description = "Initial number of nodes in the node pool (standard mode only)"
  default     = 2
}

variable "node_pool_preemptible" {
  type        = bool
  description = "Use preemptible VMs for node pool (standard mode only)"
  default     = false
}

variable "node_pool_spot" {
  type        = bool
  description = "Use spot VMs for node pool (standard mode only). Cannot be used with preemptible."
  default     = false
}

variable "node_pool_auto_repair" {
  type        = bool
  description = "Enable auto-repair for node pool (standard mode only)"
  default     = true
}

variable "node_pool_auto_upgrade" {
  type        = bool
  description = "Enable auto-upgrade for node pool (standard mode only)"
  default     = true
}

variable "node_pool_labels" {
  type        = map(string)
  description = "Labels to apply to node pool nodes (standard mode only)"
  default     = {}
}

variable "node_pool_taints" {
  type = list(object({
    key    = string
    value  = string
    effect = string
  }))
  description = "Taints to apply to node pool (standard mode only)"
  default     = []
}

