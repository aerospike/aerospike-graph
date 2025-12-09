# GCP VPC Module Outputs

output "network_name" {
  value       = local.network_name
  description = "VPC network name"
}

output "network_id" {
  value       = local.network_id
  description = "VPC network ID"
}

output "gke_subnet_name" {
  value       = google_compute_subnetwork.gke.name
  description = "GKE subnet name"
}

output "gke_subnet_id" {
  value       = google_compute_subnetwork.gke.id
  description = "GKE subnet ID"
}

output "pods_range_name" {
  value       = "${local.name_prefix}-pods"
  description = "Secondary range name for pods"
}

output "services_range_name" {
  value       = "${local.name_prefix}-services"
  description = "Secondary range name for services"
}

