# Synthetic Data Generators for Aerospike Graph Service

This repository contains synthetic data generators designed for bulk loading into [Aerospike Graph Service (AGS)](https://aerospike.com/docs/graph/). These generators produce CSV files in the format required by AGS's bulk loader.

For detailed information about the CSV format requirements, see the [Aerospike Graph Service CSV Format Documentation](https://aerospike.com/docs/graph/develop/data-loading/csv-format/).

## Table of Contents

- [Overview](#overview)
  - [Ego Network Generator (`ego-network/`)](#ego-network-generator-ego-network)
  - [Scale-Free Network Generator (`scale-free-network/`)](#scale-free-network-generator-scale-free-network)
- [Why Two Separate Generators?](#why-two-separate-generators)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
  - [Setup Virtual Environment](#setup-virtual-environment)
  - [Install Dependencies](#install-dependencies)
- [Getting Started](#getting-started)
- [Output Format](#output-format)
- [Uploading to Google Cloud Storage](#uploading-to-google-cloud-storage)
  - [Prerequisites](#prerequisites)
  - [Usage](#usage)
  - [Arguments](#arguments)
  - [Output Structure](#output-structure)

---

## Overview

This repository provides two distinct graph generators, each optimized for different graph topologies and use cases:

### Ego Network Generator (`ego-network/`)

The **Ego Network Generator** creates identity graphs using an ego-alter expansion algorithm. This generator is ideal for:

- **Identity graphs**: Graphs that model relationships around central entities (e.g., users, customers, devices)
- **Hub-and-spoke patterns**: Networks where a central "ego" node connects to multiple "alter" nodes
- **Multi-hop relationships**: Configurable expansion from ego → alter → leaf nodes
- **Schema-driven generation**: YAML-based configuration for flexible vertex and edge definitions

This generator uses configurable degree distributions (fixed, uniform, normal, poisson, lognormal) and supports parallel execution with chunking for large-scale data generation.

**Quick Start**: See [`ego-network/README.md`](ego-network/README.md) for detailed usage instructions.

### Scale-Free Network Generator (`scale-free-network/`)

The **Scale-Free Network Generator** produces power-law distributed graphs (scale-free networks). This generator is ideal for:

- **Scale-free networks**: Graphs following power-law degree distributions (e.g., social networks, web graphs)
- **Multi-type graphs**: Support for multiple vertex and edge types in a single configuration
- **Power-law tuning**: Configurable gamma parameter to control the distribution tail
- **Large-scale generation**: Parallel execution optimized for generating millions of vertices and edges

This generator uses a Zipf distribution to generate power-law degree sequences and supports full multi-type schema definitions via YAML configuration.

**Quick Start**: See [`scale-free-network/README.md`](scale-free-network/README.md) for detailed usage instructions.

## Why Two Separate Generators?

These generators serve different purposes and are optimized for different graph topologies:

1. **Different Topologies**: 
   - Ego networks create hub-and-spoke patterns around central entities
   - Scale-free networks create graphs with power-law degree distributions

2. **Different Use Cases**:
   - Ego networks are ideal for identity graphs, fraud detection, and entity resolution scenarios
   - Scale-free networks are ideal for social networks, recommendation systems, and web graph analysis

3. **Different Algorithms**:
   - Ego networks use expansion algorithms from a central node outward
   - Scale-free networks use power-law sampling to generate realistic network structures

4. **Different Configuration Models**:
   - Ego networks use a hierarchical schema (EgoNode → AlterNodes)
   - Scale-free networks use a flat multi-type schema (vertices and edges with percentages)

## Repository Structure

```
.
├── ego-network/              # Ego network generator
│   ├── README.md            # Usage documentation
│   ├── requirements.txt     # Python dependencies
│   ├── config/              # Example configuration files
│   └── generator/           # Generator source code
├── scale-free-network/      # Scale-free network generator
│   ├── README.md            # Usage documentation
│   ├── requirements.txt     # Python dependencies
│   ├── config/              # Example configuration files
│   └── generator/           # Generator source code
└── scripts/                 # Utility scripts
    ├── requirements.txt     # Script dependencies
    ├── copy_to_buckets.py  # GCS upload utility
    └── ...
```

## Requirements

Each generator and script has its own `requirements.txt` file. It's recommended to use a virtual environment to isolate dependencies.

### Setup Virtual Environment

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

### Install Dependencies

Once your virtual environment is activated, install dependencies for the generator you want to use:

```bash
# For ego network generator
cd ego-network
pip install -r requirements.txt

# For scale-free network generator
cd scale-free-network
pip install -r requirements.txt

# For utility scripts
cd scripts
pip install -r requirements.txt
```

## Getting Started

1. Choose the generator that matches your use case (see descriptions above)
2. Navigate to the generator's directory
3. Read the generator's README for detailed usage instructions
4. Configure your schema in the `config/` directory
5. Run the generator with your desired parameters

## Output Format

Both generators produce CSV files compatible with Aerospike Graph Service bulk loading:

- **Vertices**: `vertices/<vertex_type>/vertices_*.csv` with columns: `id,label,<properties...>`
- **Edges**: `edges/<edge_type>/edges_*.csv` with columns: `src_id,dst_id,label,<properties...>`

For detailed information about the CSV format, property types, and data loading, refer to the [Aerospike Graph Service CSV Format Documentation](https://aerospike.com/docs/graph/develop/data-loading/csv-format/).

## Uploading to Google Cloud Storage

After generating your data, you can upload the CSV files to a Google Cloud Storage (GCS) bucket using the `copy_to_buckets.py` utility script.

### Prerequisites

- `gsutil` installed and configured (part of [Google Cloud SDK](https://cloud.google.com/sdk/docs/install))
- Authenticated with GCP (run `gcloud auth login` and `gcloud auth application-default login`)
- Generated data files on mounted disks at `/mnt/data*` (if using the `--mount` option) or in a local directory

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

- `--gcs` **(required)**: GCS bucket path in format `gs://bucket-name/path/`
- `--threads`: Number of parallel upload threads (default: 8)
- `--disks`: Number of mounted disks to check (default: 24)

### Output Structure

The script organizes uploaded files in your GCS bucket as:
```
gs://your-bucket/path/
├── vertices/
│   └── vertices_*.csv
└── edges/
    └── edges_*.csv
```

**Note**: This script is designed to work with data generated using the `--mount` option, which distributes files across multiple mounted disks at `/mnt/data*`. For data generated to a single output directory, you may need to use `gsutil` directly or modify the script.

