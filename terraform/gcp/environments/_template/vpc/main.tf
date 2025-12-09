# VPC module instantiation

module "vpc" {
  source = "../../../modules/vpc"

  name_prefix = var.name_prefix
  environment = var.environment
  project_id  = var.project_id
  region      = var.region

  # Use existing default VPC (where Aerospike is deployed)
  use_existing_vpc  = var.use_existing_vpc
  existing_vpc_name = var.existing_vpc_name

  gke_subnet_cidr = var.gke_subnet_cidr
  pods_cidr       = var.pods_cidr
  services_cidr   = var.services_cidr
}

# Outputs for use by other modules via terraform_remote_state
output "network_name" {
  value       = module.vpc.network_name
  description = "VPC network name"
}

output "network_id" {
  value       = module.vpc.network_id
  description = "VPC network ID"
}

output "gke_subnet_name" {
  value       = module.vpc.gke_subnet_name
  description = "GKE subnet name"
}

output "pods_range_name" {
  value       = module.vpc.pods_range_name
  description = "Pods secondary range name"
}

output "services_range_name" {
  value       = module.vpc.services_range_name
  description = "Services secondary range name"
}

