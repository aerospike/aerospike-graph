# GCP VPC Module
# Creates VPC network with subnets for GKE, or uses existing VPC

locals {
  name_prefix  = var.name_prefix
  network_name = var.use_existing_vpc ? var.existing_vpc_name : google_compute_network.main[0].name
  network_id   = var.use_existing_vpc ? "projects/${var.project_id}/global/networks/${var.existing_vpc_name}" : google_compute_network.main[0].id
  common_labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# VPC Network (only created if not using existing)
resource "google_compute_network" "main" {
  count = var.use_existing_vpc ? 0 : 1

  name                    = "${local.name_prefix}-vpc"
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

# Subnet for GKE nodes
resource "google_compute_subnetwork" "gke" {
  name          = "${local.name_prefix}-gke-subnet"
  project       = var.project_id
  region        = var.region
  network       = local.network_id
  ip_cidr_range = var.gke_subnet_cidr

  # Secondary ranges for GKE pods and services
  secondary_ip_range {
    range_name    = "${local.name_prefix}-pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "${local.name_prefix}-services"
    ip_cidr_range = var.services_cidr
  }

  private_ip_google_access = true
}

# Cloud Router for NAT (always created for GKE outbound access)
resource "google_compute_router" "main" {
  name    = "${local.name_prefix}-router"
  project = var.project_id
  region  = var.region
  network = local.network_id
}

# Cloud NAT for outbound internet access from private GKE nodes
# Required for pulling container images from public registries
resource "google_compute_router_nat" "main" {
  name                               = "${local.name_prefix}-nat"
  project                            = var.project_id
  router                             = google_compute_router.main.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"

  subnetwork {
    name                    = google_compute_subnetwork.gke.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rule - allow GKE pods to reach Aerospike (for existing VPC)
resource "google_compute_firewall" "allow_gke_to_aerospike" {
  count = var.use_existing_vpc ? 1 : 0

  name    = "${local.name_prefix}-allow-gke-to-aerospike"
  project = var.project_id
  network = local.network_name

  allow {
    protocol = "tcp"
    ports    = ["3000"]  # Aerospike port
  }

  source_ranges = [var.pods_cidr]
  description   = "Allow GKE pods to reach Aerospike"
}

# Firewall rule - allow internal traffic (only for new VPC)
resource "google_compute_firewall" "allow_internal" {
  count = var.use_existing_vpc ? 0 : 1

  name    = "${local.name_prefix}-allow-internal"
  project = var.project_id
  network = local.network_name

  allow {
    protocol = "tcp"
  }

  allow {
    protocol = "udp"
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [var.gke_subnet_cidr, var.pods_cidr, var.services_cidr]
}

# Firewall rule - allow health checks from GCP load balancers
resource "google_compute_firewall" "allow_health_checks" {
  name    = "${local.name_prefix}-allow-health-checks"
  project = var.project_id
  network = local.network_name

  allow {
    protocol = "tcp"
  }

  # GCP health check IP ranges
  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
}

