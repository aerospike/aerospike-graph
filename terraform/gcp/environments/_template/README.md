# GCP Environment Template

This folder contains template files for creating new environment deployments.

## Usage

```bash
# Copy template to new environment
cp -r gcp/environments/_template gcp/environments/prod

# Update all placeholder values in the copied files (see below)
```

## Placeholder Variables

The following placeholders must be replaced with your actual values before deployment:

### Global Placeholders (all modules)

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `YOUR_TERRAFORM_STATE_BUCKET` | GCS bucket name for Terraform state | `my-company-terraform-state` |
| `YOUR_PROJECT_ID` | Your GCP project ID | `my-gcp-project-123` |
| `TODO_ENVIRONMENT` | Environment name (test, staging, prod) | `prod` |

### Naming Convention

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `ags-TODO_ENVIRONMENT` | Resource name prefix | `ags-prod` |
| `ags-TODO_ENVIRONMENT-gke` | GKE cluster name (must match in monitoring) | `ags-prod-gke` |

### Aerospike Connection (gke-cluster module)

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `TODO_AEROSPIKE_HOST` | Aerospike cluster IP/hostname | `10.128.0.5` |
| `TODO_USERNAME` | Aerospike username (if auth enabled) | `admin` |
| `TODO_PASSWORD` | Aerospike password (if auth enabled) | `secret123` |

### Docker Image (gke-cluster module)

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `gcr.io/TODO_PROJECT_ID/...` | Container image path | `gcr.io/my-project/aerospike-graph-service:3.1.1` |
| `VERSION` | Image version tag | `3.1.1-slim.1` |

## Files to Update by Module

### vpc/

| File | Placeholders |
|------|--------------|
| `backend.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` |
| `terraform.tfvars` | `ags-TODO_ENVIRONMENT`, `TODO_ENVIRONMENT`, `TODO_PROJECT_ID` |

### gke-cluster/

| File | Placeholders |
|------|--------------|
| `backend.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` |
| `main.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` (remote state) |
| `terraform.tfvars` | `ags-TODO_ENVIRONMENT`, `TODO_ENVIRONMENT`, `TODO_PROJECT_ID`, `TODO_AEROSPIKE_HOST`, `TODO_USERNAME`, `TODO_PASSWORD` |

### monitoring/

| File | Placeholders |
|------|--------------|
| `backend.tf` | `YOUR_TERRAFORM_STATE_BUCKET`, `TODO_ENVIRONMENT` |
| `terraform.tfvars` | `ags-TODO_ENVIRONMENT`, `TODO_ENVIRONMENT`, `ags-TODO_ENVIRONMENT-gke`, `TODO_PROJECT_ID` |

## Deployment Order

1. `vpc/` - Creates GKE subnet in default VPC
2. `gke-cluster/` - Creates GKE Autopilot cluster and deploys AGS
3. `monitoring/` - (Optional) Prometheus + Grafana with dashboards

## Prerequisites

1. Create GCS bucket for Terraform state:
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

4. Copy AGS Docker image to your GCR:
   ```bash
   crane copy aerospike/aerospike-graph-service:3.1.1-slim.1 \
     gcr.io/YOUR_PROJECT_ID/aerospike-graph-service:3.1.1-slim.1
   ```

