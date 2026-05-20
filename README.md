# Aerospike Graph quickstart

Welcome to the Aerospike Graph getting-started repository. This repository provides scripts, guides, and examples to help you get started with Aerospike Graph Service (AGS).

AGS is a real-time, scalable graph database that supports billions of vertices and trillions of edges with predictable low latency. AGS supports use cases such as identity graphs, fraud detection, and real-time recommendation systems. For more information, see the [Aerospike Graph documentation](https://aerospike.com/docs/graph/).

## Compatibility

- AGS requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x clients are incompatible.
- The examples in this repository are tested against the AGS image referenced in `docker-compose.yaml`. Pin a specific version (for example, `aerospike/aerospike-graph-service:3.2.2-slim.1`) for reproducible builds. See the [AGS release notes](https://aerospike.com/docs/graph/release/) for available versions.

## Start Aerospike Graph Service

```shell
docker compose up -d
```

AGS waits for Aerospike Database to finish startup before it starts.

## Query tracing with Zipkin

AGS uses [OpenZipkin](https://aerospike.com/docs/graph/operating/monitoring/query-tracing) for query tracing. The Docker Compose file in this repository includes a Zipkin service that displays query traces. After the services start, the Zipkin UI is available at [http://localhost:9411/zipkin/](http://localhost:9411/zipkin/).

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
