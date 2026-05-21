# Gremlin-JavaScript round-robin load balancer

- **Round-robin** distribution of traversal submissions across multiple Gremlin Server endpoints.
- **Health checking** and automatic detection of recovered hosts.
- **Dynamic host management** (add or remove endpoints at runtime, and remove tombstones to ensure thread safety).
- Integrates with the Gremlin-JavaScript `GraphTraversalSource`.

---

## Overview

`RoundRobinClientRemoteConnection` implements the Gremlin-JavaScript `RemoteConnection` interface, so you can write traversals as if you were connected to a single server.

---

## Why use a load balancer

Load balancers are important for high-throughput applications: they distribute work evenly instead of overloading a single node and risking CPU or I/O saturation. A load balancer also provides horizontal scalability without requiring application-code changes, because you query it as you would a single-node traversal.

---

## Prerequisites

- Node.js 14 or later.
- Gremlin driver for JavaScript. Aerospike Graph Service (AGS) requires Apache TinkerPop 3.7.x client drivers; 3.8.x and 4.0.x are incompatible.
- One or more running Gremlin Server or AGS endpoints.

---

## Usage

1. Install dependencies:

   ```shell
   npm install
   ```

2. Start the Docker containers:

   ```shell
   docker compose -f ../../common/docker-compose-load-balancer.yaml up -d
   ```

3. Run the balancer demo:

   ```shell
   npm start
   ```

---

## How it works

1. Initialization: Opens a persistent `DriverRemoteConnection` to each endpoint.
2. Round-robin: Each query picks the next available healthy connection in sequence.
3. Failure detection: On any connection or traversal error, the endpoint is marked as down (tombstoned).
4. Health loop: A background task periodically probes downed hosts with a lightweight `g.V().limit(1).toList()` query to detect recovery.
5. Recovery: If a probe succeeds, the host is marked as healthy and re-enters the rotation.

## Failure modes

If all configured endpoints become unhealthy at the same time, traversal calls fail with the underlying connection error. The health loop continues to probe downed hosts; recovered hosts re-enter the rotation automatically.
