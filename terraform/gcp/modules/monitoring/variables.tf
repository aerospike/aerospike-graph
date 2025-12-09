# Monitoring Module Variables

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
  description = "GKE cluster name (for provider configuration)"
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace for monitoring stack"
  default     = "monitoring"
}

variable "chart_version" {
  type        = string
  description = "kube-prometheus-stack Helm chart version"
  default     = "56.6.2"
}

# Grafana settings
variable "grafana_service_type" {
  type        = string
  description = "Grafana service type (LoadBalancer or ClusterIP)"
  default     = "LoadBalancer"
}

variable "grafana_admin_password" {
  type        = string
  description = "Grafana admin password"
  sensitive   = true
  default     = "admin"
}

variable "additional_datasources" {
  type        = list(any)
  description = "Additional Grafana data sources"
  default     = []
}

# Prometheus settings
variable "prometheus_retention" {
  type        = string
  description = "Prometheus data retention period"
  default     = "15d"
}

# Alertmanager
variable "alertmanager_enabled" {
  type        = bool
  description = "Enable Alertmanager"
  default     = true
}

# Aerospike dashboards
variable "deploy_aerospike_dashboards" {
  type        = bool
  description = "Deploy Aerospike Grafana dashboards"
  default     = true
}

variable "dashboards_path" {
  type        = string
  description = "Path to Aerospike dashboard JSON files"
}

# AGS scraping config
variable "ags_namespace" {
  type        = string
  description = "Namespace where Aerospike Graph Service is deployed"
  default     = "ags"
}

variable "ags_metrics_port" {
  type        = string
  description = "AGS metrics port"
  default     = "9090"
}

