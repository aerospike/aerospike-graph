# Aerospike Graph Quickstart

Welcome to the Aerospike Graph getting-started repository. This repository provides scripts, guides, and examples to help you get started with Aerospike Graph Service (AGS).

Aerospike Graph is a real-time, scalable graph database that supports billions of vertices and trillions of edges with predictable low latency. It supports use cases such as identity graphs, fraud detection, and real-time recommendation systems. For more information, see the [Aerospike Graph documentation](https://aerospike.com/docs/graph/).

## Prerequisites

- Docker and Docker Compose.
- For the root `docker-compose.yaml` stack, Aerospike Database in the compose file is **Enterprise Edition** and requires a [feature-key file](https://aerospike.com/docs/database/manage/planning/feature-key). Get a trial key from the [Aerospike Enterprise trial page](https://aerospike.com/get-started-aerospike-database/).
- As of AGS 3.2.2, AGS does not require the `graph-service` feature in the feature-key file. See [AGS 3.2.2 release notes](https://aerospike.com/docs/graph/release/3-2-2).

## Compatibility

- AGS requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x clients are incompatible.
- The root `docker-compose.yaml` uses the **standard** AGS image (`aerospike/aerospike-graph-service:latest`), which includes the [standalone bulk loader](https://aerospike.com/docs/graph/load/standalone) required for the UPI demo and Gremlin `g.call` bulk-load examples. The **slim** image does not include the bulk loader; use slim only for Gremlin-only workloads. Pin a specific version for reproducible builds (use a tag from the [AGS release notes](https://aerospike.com/docs/graph/release/)).

## Start Aerospike Graph Service

```shell
docker compose up -d
```

AGS waits for Aerospike Database to finish startup before it starts.

## Query tracing with Zipkin

AGS supports [query tracing](https://aerospike.com/docs/graph/observe/query-tracing) with [Zipkin](https://zipkin.io/). The Docker Compose file in this repository includes a Zipkin service. After the services start, the Zipkin UI is available at [http://localhost:9411/zipkin/](http://localhost:9411/zipkin/).

## Examples

This repository contains examples in multiple languages and deployment scenarios:

| Path | Description |
|------|-------------|
| [`java/basic/`](java/basic/) | Basic Java application example |
| [`nodejs/basic/`](nodejs/basic/) | Basic Node.js Express application example |
| [`nodejs/load-balancer/`](nodejs/load-balancer/) | Round-robin load balancer for Gremlin-JavaScript |
| [`golang/load-balancer/`](golang/load-balancer/) | Round-robin load balancer for Gremlin-Go |
| [`python/basic/`](python/basic/) | Basic Python example |
| [`python/transactions/`](python/transactions/) | Python web app for transaction visualization |
| [`python/food_delivery_app/`](python/food_delivery_app/) | Streamlit-based food-delivery graph demo |
| [`python/load_balancer/`](python/load_balancer/) | Round-robin load balancer for Gremlin-Python |
| [`python/tls/`](python/tls/) | Transport Layer Security (TLS) examples for AGS |
| [`misc/bulk-load-tls/`](misc/bulk-load-tls/) | Bulk loading against a TLS-enabled cluster |
| [`misc/distributed-bulkload-example/`](misc/distributed-bulkload-example/) | Distributed bulk loading on AWS EMR and GCP Dataproc |
| [`misc/multi-node-tinkerbench/`](misc/multi-node-tinkerbench/) | Multi-node benchmarking with TinkerBench on Aerolab |
| [`misc/synthetic-data-generators/`](misc/synthetic-data-generators/) | Synthetic graph data generators |
| [`misc/upi-demo/`](misc/upi-demo/) | UPI fraud-detection demo |
| [`terraform/gcp/`](terraform/gcp/) | Terraform modules to deploy AGS on Google Kubernetes Engine (GKE) |

## Contributing

Submit issues, fork the repository, and create pull requests for any improvements.
