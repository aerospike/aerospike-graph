# Gremlin Python Round-Robin Load Balancer
* **Round-robin** distribution of traversal submissions across multiple Gremlin Server endpoints
* **Health checking** and automatic detection of recovered hosts
* **Dynamic host management** (add/remove endpoints at runtime)
* Seamless integration with the Gremlin-Python `GraphTraversalSource`

---

## Overview

`RoundRobinClientRemoteConnection` implements the Gremlin-Python `RemoteConnection` interface, 
allowing you to write traversals as if you were connected to a single server:

---
## Why use a load balancer
Load balancers are crucial for high throughput applications, distributing the work evenly instead of hammering a single
node and risking CPU or I/O overloads. It also guarantees horizontal scalability without adjusting application code,
since you query it as you would a single node traversal.

---
## Prerequisites

* **Python** 3.8+
* **Gremlin-Python** driver (install with `pip install gremlinpython`)
* One or more running Gremlin Server / Aerospike Graph endpoints

---

## Usage

1. **Install dependencies**:

   ```bash
   pip install gremlinpython
2. **Start Docker Containers**
   ```shell
   docker compose up -d
   ```

3. **Run the Balancer Demo**

   ```shell
   python ./use_balancer.py
   ```
---

## How It Works

1. **Initialization**: opens a persistent `DriverRemoteConnection` to each endpoint.
2. **Round-Robin**: each traversal submission locks access, picks the next healthy connection, and dispatches.
3. **Failure Detection**: on `ClientConnectorError` or `ServerDisconnectedError`, the host is marked down.
4. **Health Loop**: a background thread periodically retries downed hosts by issuing a `g.V().limit(1)` probe.
5. **Recovery**: if the probe succeeds, the host is marked healthy and allowed to be queried again.
