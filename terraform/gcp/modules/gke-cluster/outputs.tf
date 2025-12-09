# GKE Cluster Module Outputs

output "cluster_name" {
  value       = google_container_cluster.main.name
  description = "GKE cluster name"
}

output "cluster_endpoint" {
  value       = google_container_cluster.main.endpoint
  description = "GKE cluster endpoint"
  sensitive   = true
}

output "cluster_ca_certificate" {
  value       = google_container_cluster.main.master_auth[0].cluster_ca_certificate
  description = "GKE cluster CA certificate"
  sensitive   = true
}

# Command to get credentials
output "get_credentials_command" {
  value       = "gcloud container clusters get-credentials ${google_container_cluster.main.name} --region ${var.region} --project ${var.project_id}"
  description = "Command to get kubectl credentials"
}

# Autoscaling info
output "autoscaling_enabled" {
  value       = var.enable_autoscaling
  description = "Whether HPA is enabled"
}

# Kubernetes resource outputs (available after deployment)
output "app_namespace" {
  value       = var.app_namespace
  description = "Kubernetes namespace for the application"
}

output "service_name" {
  value       = "aerospike-graph-service"
  description = "Kubernetes service name"
}

output "get_service_ip_command" {
  value       = "kubectl get svc aerospike-graph-service -n ${var.app_namespace} -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
  description = "Command to get the service external IP"
}

