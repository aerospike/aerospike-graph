package main

import (
	"log"
	"os"
	"time"

	gremlingo "github.com/apache/tinkerpop/gremlin-go/v3/driver"

	"example.com/gremlin-lb/loadbalancer"
)

func main() {
	logger := log.New(os.Stdout, "RoundRobinClientRemoteConnection ", log.LstdFlags|log.Lmsgprefix)

	endpoints := []string{"localhost:8181", "localhost:8182", "localhost:8183"}
	lb := loadbalancer.NewRoundRobinClientRemoteConnection(endpoints, "g", 10*time.Second, logger)
	defer lb.Close()

	{
		_ = lb.DoIter(func(g *gremlingo.GraphTraversalSource) <-chan error {
			return g.AddV("User").Property("userId", "U1").Property("name", "Alice").Property("age", 30).Iterate()
		})
		_ = lb.DoIter(func(g *gremlingo.GraphTraversalSource) <-chan error {
			return g.AddV("User").Property("userId", "U2").Property("name", "Bob").Property("age", 25).Iterate()
		})
		_ = lb.DoIter(func(g *gremlingo.GraphTraversalSource) <-chan error {
			return g.AddV("User").Property("userId", "U3").Property("name", "Charlie").Property("age", 35).Iterate()
		})

		_ = lb.DoIter(func(g *gremlingo.GraphTraversalSource) <-chan error {
			return g.AddV("Account").Property("accountId", "A1").Property("balance", 1000).Iterate()
		})
		_ = lb.DoIter(func(g *gremlingo.GraphTraversalSource) <-chan error {
			return g.AddV("Account").Property("accountId", "A2").Property("balance", 500).Iterate()
		})
		_ = lb.DoIter(func(g *gremlingo.GraphTraversalSource) <-chan error {
			return g.AddV("Account").Property("accountId", "A3").Property("balance", 750).Iterate()
		})

		_, _ = lb.DoList(func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error) {
			return g.V().Has("userId", "U1").As("u").V().Has("accountId", "A1").
				AddE("owns").From(gremlingo.T__.Select("u")).ToList()
		})
		_, _ = lb.DoList(func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error) {
			return g.V().Has("userId", "U2").As("u").V().Has("accountId", "A2").
				AddE("owns").From(gremlingo.T__.Select("u")).ToList()
		})
		_, _ = lb.DoList(func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error) {
			return g.V().Has("userId", "U3").As("u").V().Has("accountId", "A3").
				AddE("owns").From(gremlingo.T__.Select("u")).ToList()
		})
	}

	i := 1
	for {
		list, err := lb.DoList(func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error) {
			return g.V().Limit(i).ToList()
		})
		if err != nil {
			logger.Printf("Traversal failed: %v", err)
		} else {
			logger.Printf("Traversal result: %+v", list)
		}

		time.Sleep(3 * time.Second)
		i++
	}
}
