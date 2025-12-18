# VPC configuration
# TODO: Replace all TODO values before deployment

name_prefix = "ags-TODO_ENVIRONMENT" # TODO: Replace (e.g., 'ags-test', 'ags-prod')
environment = "TODO_ENVIRONMENT"     # TODO: Replace with environment name
project_id  = "TODO_PROJECT_ID"      # TODO: Replace with GCP project ID
region      = "us-central1"          # TODO: Adjust region if needed

# Use default VPC (same as Aerospike)
use_existing_vpc  = true
existing_vpc_name = "default"

# Network CIDRs within 10.50.0.0/16 (safe - outside default VPC's 10.128.0.0/9)
gke_subnet_cidr = "10.50.0.0/20"  # GKE nodes: 10.50.0.0  - 10.50.15.255
pods_cidr       = "10.50.16.0/20" # Pod IPs:   10.50.16.0 - 10.50.31.255
services_cidr   = "10.50.32.0/20" # Services:  10.50.32.0 - 10.50.47.255

