# GCP Terraform - Aerospike Graph Service

Terraform modules to deploy Aerospike Graph Service on GKE (Google Kubernetes Engine).

## Architecture Overview

- **GKE Autopilot** - Managed Kubernetes with ARM64 support
- **Default VPC** - Deploys alongside Aerospike database for direct connectivity
- **Autoscaling** - Horizontal Pod Autoscaler (HPA) for automatic scaling
- **Monitoring** - Optional Prometheus + Grafana with Aerospike dashboards

## Structure

```
gcp/
├── modules/                              # Reusable Terraform modules
│   ├── vpc/                              # VPC/subnet configuration
│   ├── gke-cluster/                      # GKE Autopilot + AGS deployment
│   └── monitoring/                       # Prometheus + Grafana (optional)
│       └── dashboards/                   # Aerospike Grafana dashboards
├── environments/                         # Environment configurations
│   ├── _template/                        # Template for new environments
│   └── test/                             # Test environment
│       ├── vpc/
│       ├── gke-cluster/
│       └── monitoring/
├── scripts/                              # Helper scripts (aerolab)
└── README.md
```

## Modules

| Module | Description |
|--------|-------------|
| **vpc** | Creates GKE subnet in existing VPC (default) with secondary ranges |
| **gke-cluster** | Deploys GKE Autopilot cluster with Aerospike Graph Service |
| **monitoring** | Deploys Prometheus + Grafana with pre-built Aerospike dashboards |

## Prerequisites

1. **GCP Project** with billing enabled

2. **APIs enabled**:
   - Compute Engine API
   - Kubernetes Engine API
   - Container Registry API

3. **GCS bucket** for Terraform state:
   ```bash
   gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_TERRAFORM_STATE_BUCKET
   gsutil versioning set on gs://YOUR_TERRAFORM_STATE_BUCKET
   ```

4. **Authenticate**:
   ```bash
   gcloud auth application-default login
   gcloud auth configure-docker
   ```

5. **Aerospike database** deployed in default VPC (using aerolab)

6. **Docker image** in GCR:
   ```bash
   crane copy aerospike/aerospike-graph-service:3.1.1-slim.1 \
     gcr.io/YOUR_PROJECT_ID/aerospike-graph-service:3.1.1-slim.1
   ```

## Deployment Order

| Step | Module | Description |
|------|--------|-------------|
| 1 | `vpc/` | Creates GKE subnet in default VPC |
| 2 | `gke-cluster/` | Deploys GKE Autopilot + AGS |
| 3 | `monitoring/` | *(Optional)* Prometheus + Grafana |

## Quick Start

```bash
# 1. Deploy VPC (subnet in default VPC)
cd gcp/environments/test/vpc
terraform init && terraform apply

# 2. Deploy GKE cluster + AGS
cd ../gke-cluster
terraform init && terraform apply

# 3. Get kubectl credentials
gcloud container clusters get-credentials ags-test-gke \
  --region us-central1 --project YOUR_PROJECT_ID

# 4. Get service IP
kubectl get svc aerospike-graph-service -n ags

# 5. (Optional) Deploy monitoring
cd ../monitoring
terraform init && terraform apply
```

## Key Features

### Default VPC Integration
Deploys GKE in the same VPC as Aerospike database - no VPC peering required.

### ARM64 Support
Uses GKE Autopilot Scale-Out compute class for ARM64 workloads (cost-effective).

### Autoscaling
```hcl
enable_autoscaling    = true
min_replicas          = 2
max_replicas          = 4
cpu_target_percent    = 70
```

### Monitoring Dashboards
Pre-built Grafana dashboards for:
- Aerospike Cluster metrics
- Graph Service performance
- JVM metrics
- Latency distribution
- Namespace metrics
- Node metrics

## State Management

Each module has its own state file in GCS:

| Environment | Module | GCS Path |
|-------------|--------|----------|
| test | vpc | `test/vpc/terraform.tfstate` |
| test | gke-cluster | `test/gke-cluster/terraform.tfstate` |
| test | monitoring | `test/monitoring/terraform.tfstate` |

## Creating New Environments

```bash
# Copy template
cp -r environments/_template environments/prod

# Update all placeholder values (see below)
```

### Placeholders to Replace

| Placeholder | Description | Example | Files |
|-------------|-------------|---------|-------|
| `YOUR_TERRAFORM_STATE_BUCKET` | GCS bucket for Terraform state | `my-company-tf-state` | `*/backend.tf`, `gke-cluster/main.tf` |
| `YOUR_PROJECT_ID` | GCP project ID | `my-gcp-project-123` | `*/terraform.tfvars` |
| `TODO_ENVIRONMENT` | Environment name | `prod` | `*/terraform.tfvars`, `*/backend.tf`, `gke-cluster/main.tf` |
| `ags-TODO_ENVIRONMENT` | Resource name prefix | `ags-prod` | `*/terraform.tfvars` |
| `TODO_AEROSPIKE_HOST` | Aerospike cluster IP | `10.128.0.5` | `gke-cluster/terraform.tfvars` |
| `TODO_USERNAME` | Aerospike username | `admin` | `gke-cluster/terraform.tfvars` |
| `TODO_PASSWORD` | Aerospike password | `secret` | `gke-cluster/terraform.tfvars` |

See [Template README](environments/_template/README.md) for detailed instructions.

## Endpoints

After deployment:

| Service | URL |
|---------|-----|
| Gremlin | `ws://<AGS_IP>:8182/gremlin` |
| Health | `http://<AGS_IP>:9090/healthcheck` |
| Grafana | `http://<GRAFANA_IP>:80` (if monitoring deployed) |

## Documentation

- [Template README](environments/_template/README.md) - Template usage guide
