# Gremlin Python Round-Robin Load Balancer
* **Round-robin** distribution of traversal submissions across multiple Gremlin Server endpoints
* **Health checking** and automatic detection of recovered hosts
* **Dynamic host management** (add/remove endpoints at runtime)
* Seamless integration with the Gremlin-Python `GraphTraversalSourc`

---

## Overview

`RoundRobinClientRemoteConnection` implements the Gremlin-Python `RemoteConnection` interface, allowing you to write traversals as if you were connected to a single server:

```python
  from gremlin_python.process.anonymous_traversal import traversal
  from load_balancer import RoundRobinClientRemoteConnection
  
  endpoints = ["localhost:8181", "localhost:8182", "localhost:8183"]
  rr_conn = RoundRobinClientRemoteConnection(
      endpoints,
      traversal_source="g",
      health_check_interval=10  # seconds between health probes
  )
  g = traversal().withRemote(rr_conn)
```

Under the covers, each `.submit(...)` call is forwarded to one of the configured endpoints in round-robin order. If an endpoint fails (connection refused or server disconnect), it is marked *down* and skipped on subsequent requests until a background health check succeeds.

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
 ```
2. **Run the Balancer Demo**

```python
  python use_balancer.py
```
### Basic Round-Robin

```python
  from gremlin_python.process.anonymous_traversal import traversal
  from load_balancer import RoundRobinClientRemoteConnection
  
  endpoints = ["localhost:8181", "localhost:8182", "localhost:8183"]
  rr_conn = RoundRobinClientRemoteConnection(endpoints)
  g = traversal().withRemote(rr_conn)
  
  # Submit traversals as usual
  vertices = g.V().has("status", "active").toList()
  print(vertices)
  
  # Close when done
  rr_conn.close()
```

### Dynamic Host Management

```python
  # Add a new endpoint at runtime
  rr_conn.add_host("newhost:8184")
  
  # Remove an existing endpoint
  rr_conn.remove_host("localhost:8182")
```

### Inspecting Status

```python
  # List the underlying connections
  data = rr_conn.get_clients()
  # See which hosts are currently healthy (True = up)
  health = rr_conn.get_available()
  print(data, health)
```

---

## How It Works

1. **Initialization**: opens a persistent `DriverRemoteConnection` to each endpoint.
2. **Round-Robin**: each traversal submission locks access, picks the next healthy connection, and dispatches.
3. **Failure Detection**: on `ClientConnectorError` or `ServerDisconnectedError`, the host is marked down.
4. **Health Loop**: a background thread periodically retries downed hosts by issuing a `g.V().limit(1)` probe.
5. **Recovery**: if the probe succeeds, the host is marked healthy and allowed to be queried again.
