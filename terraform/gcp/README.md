# GCP Terraform — Aerospike Graph Service

Terraform modules to deploy Aerospike Graph Service (AGS) on Google Kubernetes Engine (GKE).

> **Note:** This deployment assumes that an Aerospike Database is already deployed in GCP and is reachable at a known IP address.

## Architecture overview

- **GKE Autopilot** — managed Kubernetes with ARM64 support.
- **Default VPC** — deploys alongside Aerospike Database for direct connectivity.
- **Autoscaling** — Horizontal Pod Autoscaler (HPA) for automatic scaling.
- **Monitoring** — optional Prometheus and Grafana with Aerospike dashboards.

## Key features

### Default VPC integration

Deploys GKE in the same VPC as Aerospike Database — no VPC peering required.

### ARM64 support

Uses the GKE Autopilot Scale-Out compute class for ARM64 workloads (cost-effective).

### Autoscaling

```hcl
enable_autoscaling    = true
min_replicas          = 2
max_replicas          = 4
cpu_target_percent    = 70
```

### Monitoring dashboards

Pre-built Grafana dashboards for monitoring metrics.

## Structure

```text
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
├── scripts/                              # Helper scripts (Aerolab)
└── README.md
```

## Modules

| Module | Description |
|--------|-------------|
| `vpc` | Creates a GKE subnet in an existing VPC (default) with secondary ranges. |
| `gke-cluster` | Deploys a GKE Autopilot cluster with AGS. |
| `monitoring` | Deploys Prometheus and Grafana with pre-built Aerospike dashboards. |

## Prerequisites

1. Terraform 1.0 or later.
2. GCP project with billing enabled.
3. APIs enabled:
   - Compute Engine API.
   - Kubernetes Engine API.
   - Container Registry API.
4. GCS bucket for Terraform state:

   ```bash
   gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_TERRAFORM_STATE_BUCKET
   gsutil versioning set on gs://YOUR_TERRAFORM_STATE_BUCKET
   ```

5. Authentication:

   ```bash
   gcloud auth application-default login
   gcloud auth configure-docker
   ```

6. Aerospike Database deployed in the same VPC as the GKE cluster.
7. Docker image in GCR. Replace `VERSION` with a pinned AGS release from the [AGS release notes](https://aerospike.com/docs/graph/release/).

   ```bash
   crane copy aerospike/aerospike-graph-service:VERSION-slim \
     gcr.io/YOUR_PROJECT_ID/aerospike-graph-service:VERSION-slim
   ```

## Deployment order

> **Important:** Modules must be deployed in order. `gke-cluster` depends on `vpc` outputs, and `monitoring` depends on `gke-cluster`.

| Step | Module | Depends on | Description |
|------|--------|------------|-------------|
| 1 | `vpc/` | — | Creates GKE subnet in default VPC. |
| 2 | `gke-cluster/` | `vpc` | Deploys GKE Autopilot and AGS. |
| 3 | `monitoring/` | `gke-cluster` | *(Optional)* Prometheus and Grafana. |

## Placeholders to replace

Before deploying, replace the following placeholders in the environment files:

| Placeholder | Description | Example | Files |
|-------------|-------------|---------|-------|
| `YOUR_TERRAFORM_STATE_BUCKET` | GCS bucket for Terraform state. | `my-company-tf-state` | `*/backend.tf`, `gke-cluster/main.tf` |
| `YOUR_PROJECT_ID` | GCP project ID. | `my-gcp-project-123` | `*/terraform.tfvars` |
| `TODO_ENVIRONMENT` | Environment name. | `prod` | `*/terraform.tfvars`, `*/backend.tf`, `gke-cluster/main.tf` |
| `ags-TODO_ENVIRONMENT` | Resource name prefix. | `ags-prod` | `*/terraform.tfvars` |
| `TODO_AEROSPIKE_HOST` | Aerospike cluster IP. | `10.128.0.5` | `gke-cluster/terraform.tfvars` |
| `TODO_USERNAME` | Aerospike username. | `admin` | `gke-cluster/terraform.tfvars` |
| `TODO_PASSWORD` | Aerospike password. | `secret` | `gke-cluster/terraform.tfvars` |

> **Security:** Avoid committing sensitive values such as `TODO_PASSWORD` to version control. Use environment variables (`TF_VAR_aerospike_password`) or a secrets manager.

## Quickstart

1. Configure placeholders in all modules (see [Placeholders to replace](#placeholders-to-replace)).

   ```bash
   cd gcp/environments/test
   # Edit vpc/terraform.tfvars, vpc/backend.tf
   # Edit gke-cluster/terraform.tfvars, gke-cluster/backend.tf
   # Edit monitoring/terraform.tfvars, monitoring/backend.tf
   ```

2. Deploy the VPC (subnet in default VPC):

   ```bash
   cd vpc
   terraform init
   terraform plan
   terraform apply
   ```

3. Deploy the GKE cluster and AGS:

   ```bash
   cd ../gke-cluster
   terraform init
   terraform plan
   terraform apply
   ```

4. Get `kubectl` credentials:

   ```bash
   gcloud container clusters get-credentials ags-test-gke \
     --region us-central1 --project YOUR_PROJECT_ID
   ```

5. Get the service IP:

   ```bash
   kubectl get svc aerospike-graph-service -n ags
   ```

6. (Optional) Deploy monitoring:

   ```bash
   cd ../monitoring
   terraform init
   terraform plan
   terraform apply
   ```

## State management

Each module has its own state file in GCS:

| Environment | Module | GCS path |
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
| Grafana | `http://<GRAFANA_IP>:80` (if monitoring is deployed) |

## Cleanup and destroy

Destroy resources in reverse order to avoid dependency errors:

1. Destroy monitoring (if deployed):

   ```bash
   cd gcp/environments/test/monitoring
   terraform destroy
   ```

2. Destroy GKE cluster:

   ```bash
   cd ../gke-cluster
   terraform destroy
   ```

3. Destroy VPC subnet:

   ```bash
   cd ../vpc
   terraform destroy
   ```

## Creating new environments

```bash
# Copy template
cp -r environments/_template environments/prod

# Update all placeholder values (see "Placeholders to replace")
```

For detailed instructions, see the [template README](environments/_template/README.md).
