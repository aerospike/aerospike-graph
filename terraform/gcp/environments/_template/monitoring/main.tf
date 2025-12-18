# Monitoring stack
# Deploys Prometheus + Grafana with Aerospike dashboards

module "monitoring" {
  source = "../../../modules/monitoring"

  name_prefix  = var.name_prefix
  environment  = var.environment
  cluster_name = var.cluster_name

  # Monitoring config
  namespace              = var.namespace
  grafana_service_type   = var.grafana_service_type
  grafana_admin_password = var.grafana_admin_password
  prometheus_retention   = var.prometheus_retention
  alertmanager_enabled   = var.alertmanager_enabled

  # Aerospike dashboards
  deploy_aerospike_dashboards = var.deploy_aerospike_dashboards
  dashboards_path             = "${path.module}/../../../modules/monitoring/dashboards"

  # AGS scraping
  ags_namespace    = var.ags_namespace
  ags_metrics_port = var.ags_metrics_port
}

# Outputs
output "grafana_url" {
  value       = module.monitoring.grafana_url
  description = "Grafana URL"
}

output "get_grafana_ip_command" {
  value       = module.monitoring.get_grafana_ip_command
  description = "Command to get Grafana IP"
}

output "namespace" {
  value       = module.monitoring.namespace
  description = "Monitoring namespace"
}

