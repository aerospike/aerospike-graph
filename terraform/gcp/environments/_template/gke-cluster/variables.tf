# GKE Cluster module variables

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

# Cluster configuration
variable "release_channel" {
  type        = string
  description = "GKE release channel"
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

# Application configuration
variable "docker_image" {
  type        = string
  description = "Docker image for Aerospike Graph Service"
}

variable "cpu_architecture" {
  type        = string
  description = "CPU architecture (amd64 or arm64)"
  default     = "arm64"
}

variable "replicas" {
  type        = number
  description = "Number of replicas"
  default     = 2
}

variable "cpu_request" {
  type        = string
  description = "CPU request"
  default     = "500m"
}

variable "memory_request" {
  type        = string
  description = "Memory request"
  default     = "1Gi"
}

variable "cpu_limit" {
  type        = string
  description = "CPU limit"
  default     = "1000m"
}

variable "memory_limit" {
  type        = string
  description = "Memory limit"
  default     = "2Gi"
}

variable "enable_external_lb" {
  type        = bool
  description = "Enable external load balancer"
  default     = true
}

# Aerospike connection
variable "env_vars" {
  type        = map(string)
  description = "Environment variables for Aerospike connection"
  default     = {}
}

# Autoscaling
variable "enable_autoscaling" {
  type        = bool
  description = "Enable Horizontal Pod Autoscaler"
  default     = false
}

variable "min_replicas" {
  type        = number
  description = "Minimum replicas (HPA)"
  default     = 2
}

variable "max_replicas" {
  type        = number
  description = "Maximum replicas (HPA)"
  default     = 10
}

variable "cpu_target_percent" {
  type        = number
  description = "Target CPU utilization for autoscaling"
  default     = 70
}

variable "memory_target_percent" {
  type        = number
  description = "Target memory utilization for autoscaling"
  default     = 80
}

