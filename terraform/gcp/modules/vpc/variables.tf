# GCP VPC Module Variables

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

# Use existing VPC (default VPC where Aerospike is deployed)
variable "use_existing_vpc" {
  type        = bool
  description = "Use an existing VPC instead of creating a new one"
  default     = true
}

variable "existing_vpc_name" {
  type        = string
  description = "Name of existing VPC to use"
  default     = "default"
}

variable "gke_subnet_cidr" {
  type        = string
  description = "CIDR range for GKE nodes subnet"
  default     = "10.100.0.0/20"
}

variable "pods_cidr" {
  type        = string
  description = "CIDR range for GKE pods (secondary range)"
  default     = "10.104.0.0/14"
}

variable "services_cidr" {
  type        = string
  description = "CIDR range for GKE services (secondary range)"
  default     = "10.108.0.0/20"
}

