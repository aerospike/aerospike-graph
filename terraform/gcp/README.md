# GCP Terraform - Aerospike Graph Service

Terraform modules to deploy Aerospike Graph Service on GKE (Google Kubernetes Engine).

> **Note:** This deployment assumes an Aerospike database is deployed in GCP with an accessible IP address.

## Architecture Overview

- **GKE Autopilot** - Managed Kubernetes with ARM64 support
- **Default VPC** - Deploys alongside Aerospike database for direct connectivity
- **Autoscaling** - Horizontal Pod Autoscaler (HPA) for automatic scaling
- **Monitoring** - Optional Prometheus + Grafana with Aerospike dashboards

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
Pre-built Grafana dashboards for monitoring metrics 


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

1. **Terraform** >= 1.0

2. **GCP Project** with billing enabled

3. **APIs enabled**:
   - Compute Engine API
   - Kubernetes Engine API
   - Container Registry API

4. **GCS bucket** for Terraform state:
   ```bash
   gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_TERRAFORM_STATE_BUCKET
   gsutil versioning set on gs://YOUR_TERRAFORM_STATE_BUCKET
   ```

5. **Authenticate**:
   ```bash
   gcloud auth application-default login
   gcloud auth configure-docker
   ```

6. **Aerospike database** deployed in the same VPC as the GKE cluster

7. **Docker image** in GCR:
   ```bash
   crane copy aerospike/aerospike-graph-service:3.1.1-slim.1 \
     gcr.io/YOUR_PROJECT_ID/aerospike-graph-service:3.1.1-slim.1
   ```

## Deployment Order

> **Important:** Modules must be deployed in order. `gke-cluster` depends on `vpc` outputs, and `monitoring` depends on `gke-cluster`.

| Step | Module | Depends On | Description |
|------|--------|------------|-------------|
| 1 | `vpc/` | — | Creates GKE subnet in default VPC |
| 2 | `gke-cluster/` | `vpc` | Deploys GKE Autopilot + AGS |
| 3 | `monitoring/` | `gke-cluster` | *(Optional)* Prometheus + Grafana |

## Placeholders to Replace

Before deploying, replace the following placeholders in the environment files:

| Placeholder | Description | Example | Files |
|-------------|-------------|---------|-------|
| `YOUR_TERRAFORM_STATE_BUCKET` | GCS bucket for Terraform state | `my-company-tf-state` | `*/backend.tf`, `gke-cluster/main.tf` |
| `YOUR_PROJECT_ID` | GCP project ID | `my-gcp-project-123` | `*/terraform.tfvars` |
| `TODO_ENVIRONMENT` | Environment name | `prod` | `*/terraform.tfvars`, `*/backend.tf`, `gke-cluster/main.tf` |
| `ags-TODO_ENVIRONMENT` | Resource name prefix | `ags-prod` | `*/terraform.tfvars` |
| `TODO_AEROSPIKE_HOST` | Aerospike cluster IP | `10.128.0.5` | `gke-cluster/terraform.tfvars` |
| `TODO_USERNAME` | Aerospike username | `admin` | `gke-cluster/terraform.tfvars` |
| `TODO_PASSWORD` | Aerospike password | `secret` | `gke-cluster/terraform.tfvars` |

> **Security:** Avoid committing sensitive values like `TODO_PASSWORD` to version control. Consider using environment variables (`TF_VAR_aerospike_password`) or a secrets manager instead.

## Quick Start

```bash
# 1. Configure placeholders in all modules (see Placeholders table above)
cd gcp/environments/test
# Edit vpc/terraform.tfvars, vpc/backend.tf
# Edit gke-cluster/terraform.tfvars, gke-cluster/backend.tf
# Edit monitoring/terraform.tfvars, monitoring/backend.tf

# 2. Deploy VPC (subnet in default VPC)
cd vpc
terraform init
terraform plan    # Review changes
terraform apply

# 3. Deploy GKE cluster + AGS
cd ../gke-cluster
terraform init
terraform plan    # Review changes
terraform apply

# 4. Get kubectl credentials
gcloud container clusters get-credentials ags-test-gke \
  --region us-central1 --project YOUR_PROJECT_ID

# 5. Get service IP
kubectl get svc aerospike-graph-service -n ags

# 6. (Optional) Deploy monitoring
cd ../monitoring
terraform init
terraform plan    # Review changes
terraform apply
```

## State Management

Each module has its own state file in GCS:

| Environment | Module | GCS Path |
|-------------|--------|----------|
| test | vpc | `test/vpc/terraform.tfstate` |
| test | gke-cluster | `test/gke-cluster/terraform.tfstate` |
| test | monitoring | `test/monitoring/terraform.tfstate` |


## Endpoints

After deployment:

| Service | URL |
|---------|-----|
| Gremlin | `ws://<AGS_IP>:8182/gremlin` |
| Health | `http://<AGS_IP>:9090/healthcheck` |
| Grafana | `http://<GRAFANA_IP>:80` (if monitoring deployed) |

## Cleanup / Destroy

Destroy resources in **reverse order** to avoid dependency errors:

```bash
# 1. Destroy monitoring (if deployed)
cd gcp/environments/test/monitoring
terraform destroy

# 2. Destroy GKE cluster
cd ../gke-cluster
terraform destroy

# 3. Destroy VPC subnet
cd ../vpc
terraform destroy
```

## Creating New Environments

```bash
# Copy template
cp -r environments/_template environments/prod

# Update all placeholder values (see Placeholders to Replace section)
```

See [Template README](environments/_template/README.md) for detailed instructions.
