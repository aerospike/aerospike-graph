# GKE Cluster Module
# Creates GKE Autopilot cluster for Aerospike Graph Service

# Get access token for kubernetes provider
data "google_client_config" "default" {}

locals {
  name_prefix = var.name_prefix
  common_labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# GKE Autopilot Cluster
resource "google_container_cluster" "main" {
  name     = "${local.name_prefix}-gke"
  project  = var.project_id
  location = var.region

  # Enable Autopilot mode
  enable_autopilot = true

  network    = var.network_name
  subnetwork = var.subnet_name

  # IP allocation policy for pods and services
  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_range_name
    services_secondary_range_name = var.services_range_name
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = !var.enable_public_endpoint
    master_ipv4_cidr_block  = var.master_cidr
  }

  # Master authorized networks
  master_authorized_networks_config {
    dynamic "cidr_blocks" {
      for_each = var.authorized_networks
      content {
        cidr_block   = cidr_blocks.value.cidr
        display_name = cidr_blocks.value.name
      }
    }
  }

  # Release channel
  release_channel {
    channel = var.release_channel
  }

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  resource_labels = local.common_labels

  # Deletion protection
  deletion_protection = var.deletion_protection
}

# Kubernetes namespace for the application
resource "kubernetes_namespace" "app" {
  depends_on = [google_container_cluster.main]

  metadata {
    name = var.app_namespace
    labels = {
      environment = var.environment
    }
  }
}

# Kubernetes deployment for Aerospike Graph Service
resource "kubernetes_deployment" "ags" {
  depends_on = [kubernetes_namespace.app]

  metadata {
    name      = "aerospike-graph-service"
    namespace = var.app_namespace
    labels = {
      app = "aerospike-graph-service"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = "aerospike-graph-service"
      }
    }

    template {
      metadata {
        labels = {
          app = "aerospike-graph-service"
        }
      }

      spec {
        # Select nodes with the specified CPU architecture
        # For ARM64 in GKE Autopilot, Scale-Out compute class is required
        node_selector = var.cpu_architecture == "arm64" ? {
          "kubernetes.io/arch"              = "arm64"
          "cloud.google.com/compute-class"  = "Scale-Out"
        } : {
          "kubernetes.io/arch" = "amd64"
        }

        container {
          name  = "ags"
          image = var.docker_image

          port {
            container_port = var.container_port
            name           = "gremlin"
          }

          port {
            container_port = var.health_check_port
            name           = "health"
          }

          resources {
            requests = {
              cpu    = var.cpu_request
              memory = var.memory_request
            }
            limits = {
              cpu    = var.cpu_limit
              memory = var.memory_limit
            }
          }

          # Environment variables for Aerospike connection
          dynamic "env" {
            for_each = var.env_vars
            content {
              name  = env.key
              value = env.value
            }
          }

          liveness_probe {
            http_get {
              path = var.health_check_path
              port = var.health_check_port
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = var.health_check_path
              port = var.health_check_port
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }
        }
      }
    }
  }
}

# Kubernetes service (internal load balancer)
resource "kubernetes_service" "ags" {
  depends_on = [kubernetes_deployment.ags]

  metadata {
    name      = "aerospike-graph-service"
    namespace = var.app_namespace
    annotations = var.enable_external_lb ? {
      "cloud.google.com/load-balancer-type" = "External"
    } : {}
  }

  spec {
    type = var.enable_external_lb ? "LoadBalancer" : "ClusterIP"

    selector = {
      app = "aerospike-graph-service"
    }

    port {
      name        = "gremlin"
      port        = var.container_port
      target_port = var.container_port
    }

    port {
      name        = "health"
      port        = var.health_check_port
      target_port = var.health_check_port
    }
  }
}

# Horizontal Pod Autoscaler
resource "kubernetes_horizontal_pod_autoscaler_v2" "ags" {
  count      = var.enable_autoscaling ? 1 : 0
  depends_on = [kubernetes_deployment.ags]

  metadata {
    name      = "aerospike-graph-service-hpa"
    namespace = var.app_namespace
  }

  spec {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.ags.metadata[0].name
    }

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = var.cpu_target_percent
        }
      }
    }

    metric {
      type = "Resource"
      resource {
        name = "memory"
        target {
          type                = "Utilization"
          average_utilization = var.memory_target_percent
        }
      }
    }

    behavior {
      scale_down {
        stabilization_window_seconds = var.scale_down_stabilization_seconds
        select_policy                = "Min"
        policy {
          type           = "Percent"
          value          = 10
          period_seconds = 60
        }
      }
      scale_up {
        stabilization_window_seconds = 0
        select_policy                = "Max"
        policy {
          type           = "Percent"
          value          = 100
          period_seconds = 15
        }
        policy {
          type           = "Pods"
          value          = 4
          period_seconds = 15
        }
      }
    }
  }
}

