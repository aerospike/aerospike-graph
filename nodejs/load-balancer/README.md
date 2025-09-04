# Gremlin Javascript Round-Robin Load Balancer
* **Round-robin** distribution of traversal submissions across multiple Gremlin Server endpoints
* **Health checking** and automatic detection of recovered hosts
* **Dynamic host management** (add/remove endpoints at runtime, remove tombstones to ensure thread safety)
* Seamless integration with the Gremlin-Javascript `GraphTraversalSource`

---

## Overview

`RoundRobinClientRemoteConnection` implements the Gremlin-Javascript `RemoteConnection` interface, 
allowing you to write traversals as if you were connected to a single server:

---
## Why use a load balancer
Load balancers are crucial for high throughput applications, distributing the work evenly instead of hammering a single
node and risking CPU or I/O overloads. It also guarantees horizontal scalability without adjusting application code,
since you query it as you would a single node traversal.

---
## Prerequisites

* **Node** 14+
* **Gremlin** driver for javascript
* One or more running Gremlin Server / Aerospike Graph endpoints

---

## Usage

1. **Install dependencies**:

   ```shell
   npm install
2. **Start Docker Containers**
   ```shell
   docker compose up -d

3. **Run the Balancer Demo**

   ```shell
   npm start

---

## How It Works

1. **Initialization**: opens a persistent `DriverRemoteConnection` to each endpoint.
2. **Round-Robin**: Each query picks the next available healthy connection in sequence.
3. **Failure Detection**: On any connection or traversal error, the endpoint is marked down (tombstoned).
4. **Health Loop**: A background task periodically probes downed hosts with a lightweight `g.V().limit(1).toList()` query to detect recovery.
5. **Recovery**: If a probe succeeds, the host is marked healthy and re-enters the rotation.
