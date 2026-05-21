# GCP environment template

This folder contains template files for creating new environment deployments.

## Usage

```bash
# Copy template to new environment
cp -r gcp/environments/_template gcp/environments/prod

# Update all placeholder values in the copied files (see the following sections)
```

## Placeholder variables

The following placeholders must be replaced with your actual values before deployment:

### Global placeholders (all modules)

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `YOUR_TERRAFORM_STATE_BUCKET` | GCS bucket name for Terraform state. | `my-company-terraform-state` |
| `YOUR_PROJECT_ID` | Your GCP project ID. | `my-gcp-project-123` |
| `TODO_ENVIRONMENT` | Environment name (`test`, `staging`, `prod`). | `prod` |

### Naming convention

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `ags-TODO_ENVIRONMENT` | Resource name prefix. | `ags-prod` |
| `ags-TODO_ENVIRONMENT-gke` | GKE cluster name (must match in monitoring). | `ags-prod-gke` |

### Aerospike connection (`gke-cluster` module)

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `TODO_AEROSPIKE_HOST` | Aerospike cluster IP or hostname. | `10.128.0.5` |
| `TODO_USERNAME` | Aerospike username (if authentication is enabled). | `admin` |
| `TODO_PASSWORD` | Aerospike password (if authentication is enabled). | `secret123` |

### Docker image (`gke-cluster` module)

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `gcr.io/TODO_PROJECT_ID/...` | Container image path. | `gcr.io/my-project/aerospike-graph-service:3.2.2` |
| `VERSION` | Image version tag. | `3.2.2-slim.1` |

## Files to update by module

### `vpc/`

| File | Placeholders |
|------|--------------|
| `backend.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` |
| `terraform.tfvars` | `ags-TODO_ENVIRONMENT`, `TODO_ENVIRONMENT`, `TODO_PROJECT_ID` |

### `gke-cluster/`

| File | Placeholders |
|------|--------------|
| `backend.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` |
| `main.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` (remote state) |
| `terraform.tfvars` | `ags-TODO_ENVIRONMENT`, `TODO_ENVIRONMENT`, `TODO_PROJECT_ID`, `TODO_AEROSPIKE_HOST`, `TODO_USERNAME`, `TODO_PASSWORD` |

### `monitoring/`

| File | Placeholders |
|------|--------------|
| `backend.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` |
| `terraform.tfvars` | `ags-TODO_ENVIRONMENT`, `TODO_ENVIRONMENT`, `ags-TODO_ENVIRONMENT-gke`, `TODO_PROJECT_ID` |

## Deployment order

1. `vpc/` — creates GKE subnet in default VPC.
2. `gke-cluster/` — creates GKE Autopilot cluster and deploys AGS.
3. `monitoring/` — *(Optional)* Prometheus and Grafana with dashboards.

## Prerequisites

1. Create a GCS bucket for Terraform state:

   ```bash
   gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_TERRAFORM_STATE_BUCKET
   gsutil versioning set on gs://YOUR_TERRAFORM_STATE_BUCKET
   ```

2. Enable required GCP APIs:

   ```bash
   gcloud services enable compute.googleapis.com
   gcloud services enable container.googleapis.com
   ```

3. Authenticate with GCP:

   ```bash
   gcloud auth application-default login
   ```

4. Copy the AGS Docker image to your GCR. Replace `VERSION` with a pinned AGS release from the [AGS release notes](https://aerospike.com/docs/graph/release/).

   ```bash
   crane copy aerospike/aerospike-graph-service:VERSION-slim \
     gcr.io/YOUR_PROJECT_ID/aerospike-graph-service:VERSION-slim
   ```
