terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "YOUR_TERRAFORM_STATE_BUCKET"
    prefix = "TODO_ENVIRONMENT/vpc" # TODO: Replace with environment name
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

