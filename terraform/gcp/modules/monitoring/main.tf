# Monitoring Module for GKE
# Deploys Prometheus + Grafana with custom Aerospike dashboards

locals {
  name_prefix = var.name_prefix
}

# Deploy kube-prometheus-stack via Helm
resource "helm_release" "monitoring" {
  name             = "monitoring"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = var.chart_version
  namespace        = var.namespace
  create_namespace = true
  timeout          = 600

  values = [
    yamlencode({
      # Grafana configuration
      grafana = {
        enabled = true
        service = {
          type = var.grafana_service_type
        }
        adminPassword = var.grafana_admin_password
        
        # Sidecar to load dashboards from ConfigMaps
        sidecar = {
          dashboards = {
            enabled = true
            label   = "grafana_dashboard"
          }
        }
        
        # Data sources
        additionalDataSources = var.additional_datasources
      }
      
      # Prometheus configuration
      prometheus = {
        prometheusSpec = {
          retention = var.prometheus_retention
          
          # Scrape Aerospike Graph Service metrics
          additionalScrapeConfigs = [
            {
              job_name        = "aerospike-graph-service"
              scrape_interval = "15s"
              kubernetes_sd_configs = [{
                role = "pod"
                namespaces = {
                  names = [var.ags_namespace]
                }
              }]
              relabel_configs = [
                {
                  source_labels = ["__meta_kubernetes_pod_label_app"]
                  action        = "keep"
                  regex         = "aerospike-graph-service"
                },
                {
                  source_labels = ["__meta_kubernetes_pod_container_port_number"]
                  action        = "keep"
                  regex         = var.ags_metrics_port
                }
              ]
            }
          ]
        }
      }
      
      # Alertmanager
      alertmanager = {
        enabled = var.alertmanager_enabled
      }
      
      # Disable node exporter - not supported on GKE Autopilot (DaemonSets restricted)
      nodeExporter = {
        enabled = false
      }
      
      # Kube-state-metrics - deploy in monitoring namespace
      kubeStateMetrics = {
        enabled = true
      }
      
      # ============================================
      # GKE Autopilot Compatibility Settings
      # ============================================
      # Disable components that require kube-system access
      
      # Disable kube-proxy metrics (requires kube-system)
      kubeProxy = {
        enabled = false
      }
      
      # Disable CoreDNS metrics (requires kube-system)
      coreDns = {
        enabled = false
      }
      
      # Disable kube-controller-manager metrics (requires kube-system)
      kubeControllerManager = {
        enabled = false
      }
      
      # Disable kube-scheduler metrics (requires kube-system)
      kubeScheduler = {
        enabled = false
      }
      
      # Disable kube-etcd metrics (requires kube-system)
      kubeEtcd = {
        enabled = false
      }
      
      # Disable kubeDns metrics (requires kube-system)
      kubeDns = {
        enabled = false
      }
      
      # Prometheus Operator - don't try to scrape kube-system components
      prometheusOperator = {
        admissionWebhooks = {
          # Use certManager or disable
          enabled = true
          patch = {
            enabled = true
          }
        }
        # Don't create services in kube-system
        kubeletService = {
          enabled = false
        }
      }
    })
  ]
}

# Create ConfigMaps for custom Aerospike dashboards
resource "kubernetes_config_map" "dashboard_cluster" {
  count = var.deploy_aerospike_dashboards ? 1 : 0

  metadata {
    name      = "grafana-dashboard-aerospike-cluster"
    namespace = var.namespace
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "cluster.json" = file("${var.dashboards_path}/cluster.json")
  }

  depends_on = [helm_release.monitoring]
}

resource "kubernetes_config_map" "dashboard_graph_service" {
  count = var.deploy_aerospike_dashboards ? 1 : 0

  metadata {
    name      = "grafana-dashboard-graph-service"
    namespace = var.namespace
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "graph_service_view.json" = file("${var.dashboards_path}/graph_service_view.json")
  }

  depends_on = [helm_release.monitoring]
}

resource "kubernetes_config_map" "dashboard_graph_service_jvm" {
  count = var.deploy_aerospike_dashboards ? 1 : 0

  metadata {
    name      = "grafana-dashboard-graph-service-jvm"
    namespace = var.namespace
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "graph_service_jvmview.json" = file("${var.dashboards_path}/graph_service_jvmview.json")
  }

  depends_on = [helm_release.monitoring]
}

resource "kubernetes_config_map" "dashboard_latency" {
  count = var.deploy_aerospike_dashboards ? 1 : 0

  metadata {
    name      = "grafana-dashboard-latency"
    namespace = var.namespace
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "latency.json" = file("${var.dashboards_path}/latency.json")
  }

  depends_on = [helm_release.monitoring]
}

resource "kubernetes_config_map" "dashboard_namespace" {
  count = var.deploy_aerospike_dashboards ? 1 : 0

  metadata {
    name      = "grafana-dashboard-namespace"
    namespace = var.namespace
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "namespace.json" = file("${var.dashboards_path}/namespace.json")
  }

  depends_on = [helm_release.monitoring]
}

resource "kubernetes_config_map" "dashboard_node" {
  count = var.deploy_aerospike_dashboards ? 1 : 0

  metadata {
    name      = "grafana-dashboard-node"
    namespace = var.namespace
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "node.json" = file("${var.dashboards_path}/node.json")
  }

  depends_on = [helm_release.monitoring]
}

