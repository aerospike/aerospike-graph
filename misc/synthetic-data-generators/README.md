# Synthetic data generators for Aerospike Graph Service (AGS)

This repository contains synthetic data generators for bulk loading into [Aerospike Graph Service (AGS)](https://aerospike.com/docs/graph/). The generators produce CSV files in the format required by the AGS bulk loader.

For detailed information about the CSV format requirements, see the [AGS CSV format documentation](https://aerospike.com/docs/graph/load/csv-format).

## Table of contents

- [Overview](#overview)
  - [Ego network generator (`ego-network/`)](#ego-network-generator-ego-network)
  - [Scale-free network generator (`scale-free-network/`)](#scale-free-network-generator-scale-free-network)
- [Why two separate generators?](#why-two-separate-generators)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
  - [Set up a virtual environment](#set-up-a-virtual-environment)
  - [Install dependencies](#install-dependencies)
- [Getting started](#getting-started)
- [Output format](#output-format)
- [Uploading to Google Cloud Storage](#uploading-to-google-cloud-storage)
  - [Prerequisites](#prerequisites)
  - [Usage](#usage)
  - [Arguments](#arguments)
  - [Output structure](#output-structure)

---

## Overview

This repository provides two distinct graph generators, each optimized for a different graph topology and set of use cases:

### Ego network generator (`ego-network/`)

The ego network generator creates identity graphs using an ego-alter expansion algorithm. This generator is suitable for:

- **Identity graphs:** graphs that model relationships around central entities (for example, users, customers, devices).
- **Hub-and-spoke patterns:** networks where a central "ego" node connects to multiple "alter" nodes.
- **Multi-hop relationships:** configurable expansion from ego → alter → leaf nodes.
- **Schema-driven generation:** YAML-based configuration for vertex and edge definitions.

The generator uses configurable degree distributions (`fixed`, `uniform`, `normal`, `poisson`, `lognormal`) and supports parallel execution with chunking for large-scale data generation.

For detailed usage instructions, see [`ego-network/README.md`](ego-network/README.md).

### Scale-free network generator (`scale-free-network/`)

The scale-free network generator produces power-law–distributed graphs. This generator is suitable for:

- **Scale-free networks:** graphs following power-law degree distributions (for example, social networks, web graphs).
- **Multi-type graphs:** support for multiple vertex and edge types in a single configuration.
- **Power-law tuning:** configurable gamma parameter to control the distribution tail.
- **Large-scale generation:** parallel execution optimized for generating millions of vertices and edges.

The generator uses a Zipf distribution to generate power-law degree sequences and supports full multi-type schema definitions in YAML.

For detailed usage instructions, see [`scale-free-network/README.md`](scale-free-network/README.md).

## Why two separate generators?

The two generators serve different purposes and are optimized for different graph topologies:

1. Different topologies:
   - Ego networks create hub-and-spoke patterns around central entities.
   - Scale-free networks create graphs with power-law degree distributions.

2. Different use cases:
   - Ego networks are suitable for identity graphs, fraud detection, and entity-resolution scenarios.
   - Scale-free networks are suitable for social networks, recommendation systems, and web-graph analysis.

3. Different algorithms:
   - Ego networks use expansion algorithms from a central node outward.
   - Scale-free networks use power-law sampling to generate realistic network structures.

4. Different configuration models:
   - Ego networks use a hierarchical schema (`EgoNode → AlterNodes`).
   - Scale-free networks use a flat multi-type schema (vertices and edges with percentages).

## Repository structure

```text
.
├── ego-network/              # Ego network generator
│   ├── README.md             # Usage documentation
│   ├── requirements.txt      # Python dependencies
│   ├── config/               # Example configuration files
│   └── generator/            # Generator source code
├── scale-free-network/       # Scale-free network generator
│   ├── README.md             # Usage documentation
│   ├── requirements.txt      # Python dependencies
│   ├── config/               # Example configuration files
│   └── generator/            # Generator source code
└── scripts/                  # Utility scripts
    ├── requirements.txt      # Script dependencies
    ├── copy_to_buckets.py    # GCS upload utility
    └── ...
```

## Requirements

Each generator and script has its own `requirements.txt` file. We recommend using a virtual environment to isolate dependencies.

### Set up a virtual environment

Create and activate a virtual environment before installing dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### Install dependencies

After your virtual environment is active, install the dependencies for the generator you want to use:

```bash
# For the ego network generator
cd ego-network
pip install -r requirements.txt

# For the scale-free network generator
cd scale-free-network
pip install -r requirements.txt

# For the utility scripts
cd scripts
pip install -r requirements.txt
```

## Getting started

1. Choose the generator that matches your use case (see the preceding descriptions).
2. Open the generator directory and follow its README for detailed usage instructions.
3. Configure your schema in the `config/` directory.
4. Run the generator with your chosen parameters.

## Output format

Both generators produce CSV files compatible with AGS bulk loading:

- **Vertices:** `vertices/<vertex_type>/vertices_*.csv` with columns: `~id`, `~label`, `<properties...>`.
- **Edges:** `edges/<edge_type>/edges_*.csv` with columns: `~from`, `~to`, `~label`, `<properties...>`.

For detailed information about the CSV format, property types, and data loading, see the [AGS CSV format documentation](https://aerospike.com/docs/graph/load/csv-format).

## Uploading to Google Cloud Storage

After generating your data, you can upload the CSV files to a Google Cloud Storage (GCS) bucket using the `copy_to_buckets.py` utility script.

### Prerequisites

- `gsutil` installed and configured (part of the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)).
- Authenticated with GCP (run `gcloud auth login` and `gcloud auth application-default login`).
- Generated data files on mounted disks at `/mnt/data*` (for use with the `--mount` option) or in a local directory.

### Usage

The script uploads vertices and edges from mounted disks to your GCS bucket:

```bash
cd scripts
pip install -r requirements.txt

# Upload from mounted disks to GCS
python copy_to_buckets.py \
  --gcs gs://your-bucket-name/path/to/data \
  --threads 8 \
  --disks 24
```

### Arguments

- `--gcs` **(required):** GCS bucket path in the format `gs://bucket-name/path/`.
- `--threads`: number of parallel upload threads (default: 8).
- `--disks`: number of mounted disks to check (default: 24).

### Output structure

The script organizes uploaded files in your GCS bucket as:

```text
gs://your-bucket/path/
├── vertices/
│   └── vertices_*.csv
└── edges/
    └── edges_*.csv
```

> **Note:** This script is designed to work with data generated using the `--mount` option, which distributes files across multiple mounted disks at `/mnt/data*`. For data generated to a single output directory, use `gsutil` directly or modify the script.
