# GKE Cluster module instantiation

# Get VPC outputs from vpc module state
data "terraform_remote_state" "vpc" {
  backend = "gcs"
  config = {
    bucket = "YOUR_TERRAFORM_STATE_BUCKET"
    prefix = "TODO_ENVIRONMENT/vpc" # TODO: Replace with environment name
  }
}

module "gke_cluster" {
  source = "../../../modules/gke-cluster"

  name_prefix = var.name_prefix
  environment = var.environment
  project_id  = var.project_id
  region      = var.region
  zones       = var.zones

  # Network from VPC module
  network_name        = data.terraform_remote_state.vpc.outputs.network_name
  subnet_name         = data.terraform_remote_state.vpc.outputs.gke_subnet_name
  pods_range_name     = data.terraform_remote_state.vpc.outputs.pods_range_name
  services_range_name = data.terraform_remote_state.vpc.outputs.services_range_name

  # Cluster configuration
  release_channel        = var.release_channel
  deletion_protection    = var.deletion_protection
  enable_public_endpoint = var.enable_public_endpoint

  # Application configuration
  docker_image       = var.docker_image
  cpu_architecture   = var.cpu_architecture
  replicas           = var.replicas
  cpu_request        = var.cpu_request
  memory_request     = var.memory_request
  cpu_limit          = var.cpu_limit
  memory_limit       = var.memory_limit
  enable_external_lb = var.enable_external_lb

  # Aerospike connection
  env_vars = var.env_vars

  # Autoscaling
  enable_autoscaling    = var.enable_autoscaling
  min_replicas          = var.min_replicas
  max_replicas          = var.max_replicas
  cpu_target_percent    = var.cpu_target_percent
  memory_target_percent = var.memory_target_percent
}

# Outputs
output "cluster_name" {
  value       = module.gke_cluster.cluster_name
  description = "GKE cluster name"
}

output "get_credentials_command" {
  value       = module.gke_cluster.get_credentials_command
  description = "Command to get kubectl credentials"
}

output "get_service_ip_command" {
  value       = module.gke_cluster.get_service_ip_command
  description = "Command to get the service external IP"
}

