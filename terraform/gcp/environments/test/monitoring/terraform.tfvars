# Monitoring configuration for test environment

name_prefix  = "ags-test"
environment  = "test"
cluster_name = "ags-test-gke"
project_id   = "YOUR_PROJECT_ID"
region       = "us-central1"

# Monitoring settings
namespace              = "monitoring"
grafana_service_type   = "LoadBalancer" # Use ClusterIP for internal only
grafana_admin_password = "changeme"     # TODO: Change in production!
prometheus_retention   = "15d"
alertmanager_enabled   = true

# Aerospike dashboards
deploy_aerospike_dashboards = true
ags_namespace               = "ags"
ags_metrics_port            = "9090"

