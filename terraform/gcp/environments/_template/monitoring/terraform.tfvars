# Monitoring configuration
# TODO: Replace all TODO values before deployment

name_prefix  = "ags-TODO_ENVIRONMENT" # TODO: Replace (e.g., 'ags-test', 'ags-prod')
environment  = "TODO_ENVIRONMENT"     # TODO: Replace with environment name
cluster_name = "ags-TODO_ENVIRONMENT-gke" # TODO: Must match GKE cluster name
project_id   = "TODO_PROJECT_ID"      # TODO: Replace with GCP project ID
region       = "us-central1"          # TODO: Adjust region if needed

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

