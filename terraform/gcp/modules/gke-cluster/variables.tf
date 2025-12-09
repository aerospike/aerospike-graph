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

