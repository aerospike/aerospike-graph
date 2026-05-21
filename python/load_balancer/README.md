# Gremlin-Python round-robin load balancer

- **Round-robin** distribution of traversal submissions across multiple Gremlin Server endpoints.
- **Health checking** and automatic detection of recovered hosts.
- **Dynamic host management** (add or remove endpoints at runtime).
- Integrates with the Gremlin-Python `GraphTraversalSource`.

---

## Overview

`RoundRobinClientRemoteConnection` implements the Gremlin-Python `RemoteConnection` interface, so you can write traversals as if you were connected to a single server.

---

## Why use a load balancer

Load balancers are important for high-throughput applications: they distribute work evenly instead of overloading a single node and risking CPU or I/O saturation. A load balancer also provides horizontal scalability without requiring application-code changes, because you query it as you would a single-node traversal.

---

## Prerequisites

- Python 3.9 or later.
- Gremlin-Python driver (`gremlinpython`). Aerospike Graph Service (AGS) requires Apache TinkerPop 3.7.x client drivers; 3.8.x and 4.0.x are incompatible.
- One or more running Gremlin Server or AGS endpoints.

---

## Usage

1. Install dependencies:

   ```bash
   pip install "gremlinpython>=3.7.0,<3.8.0"
   ```

2. Start the Docker containers:

   ```shell
   docker compose -f ../../common/docker-compose-load-balancer.yaml up -d
   ```

3. Run the balancer demo:

   ```shell
   python ./use_balancer.py
   ```

---

## How it works

1. Initialization: Opens a persistent `DriverRemoteConnection` to each endpoint.
2. Round-robin: Each traversal submission acquires a lock, picks the next healthy connection, and dispatches.
3. Failure detection: On `ClientConnectorError` or `ServerDisconnectedError`, the host is marked as down.
4. Health loop: A background thread periodically retries downed hosts by issuing a `g.V().limit(1)` probe.
5. Recovery: If the probe succeeds, the host is marked as healthy and re-enters the rotation.

## Failure modes

If all configured endpoints become unhealthy at the same time, traversal calls raise the underlying connection error. The health loop continues to probe downed hosts; recovered hosts re-enter the rotation automatically.
