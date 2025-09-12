# Gremlin Go Round-Robin Load Balancer

* **Round-robin** distribution of traversal submissions across multiple Gremlin Server endpoints
* **Health checking** and automatic detection of recovered hosts
* **Dynamic host management** (add/remove endpoints at runtime)
* Uses the Gremlin-go `DriverRemoteConnection`

---
## Overview
`RoundRobinClientRemoteConnection` exposes its own api for queries and load balances traversals sent.

---
## Why use a load balancer
Load balancers are crucial for high throughput applications, distributing the work evenly instead of hammering a single
node and risking CPU or I/O overloads. It also guarantees horizontal scalability without adjusting application code,
since you query it as you would a single node traversal.

---
## Prerequisites

* **go** 1.22+
* One or more running Gremlin Server / Aerospike Graph endpoints

---
## Usage

1. **Start the Docker Containers**:

    ```shell
    docker compose -f ..\..\common\docker-compose-load-balancer.yaml up -d
   ```
2. **Tidy the mod file**

   ```shell
   go mod tidy
   ```
3. **Run the Balancer Demo**

   ```shell
   go run ./cmd/use_balancer
   ```
---
## How it Works
Unlike gremlin-python, in gremlin-go `withRemote()` accepts a set type of `*DriverRemoteConnection`, meaning we cannot 
pass our own balancer object that implements an interface into it like the python load balancer example. 
Thus this load-balancer instead exposes its own api, where you choose the function that matches the return type of your 
traversal, such as `DoList` for traversals returning results
```go
func (lb *RoundRobinClientRemoteConnection) DoList(
	f func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error),
) ([]*gremlingo.Result, error)
``` 
and `DoIter` for side-effect queries that return an async error channel.
```go
func (lb *RoundRobinClientRemoteConnection) DoIter(
	f func(g *gremlingo.GraphTraversalSource) <-chan error,
) error
```

In a custom load balancer another implementation you could create would be where the user has to request a new
traversal source from the load balancer every time they want to rotate which would give the advantage of querying
normally as you would with a single DRC, at the cost of the rotation not being executed when calling a query.