# Monitoring variables for test environment

variable "name_prefix" {
  type        = string
  description = "Prefix for all resource names (e.g., 'ags-test', 'ags-prod')"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "cluster_name" {
  type        = string
  description = "GKE cluster name"
}

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
}

# Monitoring configuration
variable "namespace" {
  type        = string
  description = "Kubernetes namespace for monitoring"
  default     = "monitoring"
}

variable "grafana_service_type" {
  type        = string
  description = "Grafana service type"
  default     = "LoadBalancer"
}

variable "grafana_admin_password" {
  type        = string
  description = "Grafana admin password"
  sensitive   = true
  default     = "admin"
}

variable "prometheus_retention" {
  type        = string
  description = "Prometheus data retention"
  default     = "15d"
}

variable "alertmanager_enabled" {
  type        = bool
  description = "Enable Alertmanager"
  default     = true
}

# Aerospike dashboards
variable "deploy_aerospike_dashboards" {
  type        = bool
  description = "Deploy Aerospike dashboards"
  default     = true
}

variable "ags_namespace" {
  type        = string
  description = "AGS namespace"
  default     = "ags"
}

variable "ags_metrics_port" {
  type        = string
  description = "AGS metrics port"
  default     = "9090"
}

