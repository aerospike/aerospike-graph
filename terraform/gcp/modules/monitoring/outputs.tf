# Monitoring Module Outputs

output "grafana_service_name" {
  value       = "monitoring-grafana"
  description = "Grafana service name"
}

output "prometheus_service_name" {
  value       = "monitoring-kube-prometheus-prometheus"
  description = "Prometheus service name"
}

output "namespace" {
  value       = var.namespace
  description = "Monitoring namespace"
}

output "get_grafana_ip_command" {
  value       = "kubectl get svc monitoring-grafana -n ${var.namespace} -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
  description = "Command to get Grafana external IP"
}

output "grafana_url" {
  value       = "http://<GRAFANA_IP>:80"
  description = "Grafana URL (replace <GRAFANA_IP> with actual IP)"
}

