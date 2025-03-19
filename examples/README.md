# Aerospike Graph QuickStart

Welcome to the Aerospike Graph getting started folder! This folder provides scripts, guides, and examples designed to help you get started with Aerospike Graph.

Aerospike Graph is a developer-ready, real-time, scalable graph database built to support billions of vertices and trillions of edges with predicable low latency, making it ideal for use cases such as identity graphs, fraud detection, and real-time recommendation systems. For in-depth information about Aerospike Graph and its capabilities, please refer to the official Aerospike Graph documentation.

# To start Aerospike Graph
```shell

TODO: add build.sh in here.

docker compose up -d
```
Please note that Graph will wait for the database to complete start up before it attempts to start.


Navigate to the examples folder and try out the examples in different languages
```shell
cd examples
```

# Query tracing with Zipkin

Aerospike Graph utilizes Zipkin for query tracing [OpenZipkin](https://aerospike.com/docs/graph/operating/monitoring/query-tracing).
This docker compose file includes a Zipkin service that show query traces. Once the services have started the Zipkin UI is available at http://localhost:9411/zipkin/.
