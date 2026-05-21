# Gremlin-Go round-robin load balancer

Round-robin load balancing for Gremlin-Go clients connecting to Aerospike Graph Service (AGS) or Gremlin Server endpoints.

- **Round-robin** distribution of traversal submissions across multiple Gremlin Server endpoints.
- **Health checking** and automatic detection of recovered hosts.
- **Dynamic host management** (add or remove endpoints at runtime).
- Uses the Gremlin-Go `DriverRemoteConnection`.

---

## Overview

`RoundRobinClientRemoteConnection` exposes its own API for queries and load-balances submitted traversals.

---

## Why use a load balancer

Load balancers are important for high-throughput applications. They distribute work evenly instead of overloading a single node and risking CPU or I/O saturation. A load balancer also provides horizontal scalability without requiring application-code changes, because you query all nodes as you would a single-node traversal.

---

## Prerequisites

- Go 1.22 or later.
- One or more running Gremlin Server or Aerospike Graph Service (AGS) endpoints.

> **Note:** AGS requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x are incompatible.

---

## Usage

1. Start the Docker containers:

   ```shell
   docker compose -f ../../common/docker-compose-load-balancer.yaml up -d
   ```

2. Tidy the Go module file:

   ```shell
   go mod tidy
   ```

3. Run the balancer demo:

   ```shell
   go run ./cmd/use_balancer
   ```

---

## How it works

Gremlin-Go's `withRemote()` accepts only `*DriverRemoteConnection`, so you cannot inject a custom load-balancing wrapper through the standard remote connection API. Instead, this load balancer exposes its own API. Choose the function that matches the return type of your traversal, such as `DoList` for traversals returning results:

```go
func (lb *RoundRobinClientRemoteConnection) DoList(
    f func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error),
) ([]*gremlingo.Result, error)
```

Use `DoIter` for side-effect queries that return an asynchronous error channel:

```go
func (lb *RoundRobinClientRemoteConnection) DoIter(
    f func(g *gremlingo.GraphTraversalSource) <-chan error,
) error
```

An alternative implementation could require a request for a new traversal source from the load balancer for each rotation. That approach lets you query as you would with a single `DriverRemoteConnection`, at the cost of not rotating mid-query.
