package tests

import (
	"bytes"
	"errors"
	"fmt"
	"log"
	"net"
	"os/exec"
	"strings"
	"testing"
	"time"

	"example.com/gremlin-lb/loadbalancer"
	gremlingo "github.com/apache/tinkerpop/gremlin-go/v3/driver"
)

var endpoints = []string{"localhost:8181", "localhost:8182", "localhost:8183"}

func setupGraph(t *testing.T, lb *loadbalancer.RoundRobinClientRemoteConnection) {
	t.Helper()

	{
		_ = lb.DoIter(func(g *gremlingo.GraphTraversalSource) <-chan error {
			return g.V().Drop().Iterate()
		})

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

	// Start rotation from #0 for deterministic tests
	lb.SetNextIndex(0)
}

func newLogger(buf *bytes.Buffer) *log.Logger {
	return log.New(buf, "", 0)
}

func TestHostAddAndRemoval(t *testing.T) {
	buf := &bytes.Buffer{}
	lb := loadbalancer.NewRoundRobinClientRemoteConnection(endpoints, "g", 2*time.Second, newLogger(buf))
	defer lb.Close()

	initialHosts := lb.GetClients()
	initialAvail := lb.GetAvailable()

	toRemove := endpoints[1]
	lb.RemoveHost(toRemove)

	postRemoveHosts := lb.GetClients()
	postRemoveAvail := lb.GetAvailable()

	removed := true
	for _, h := range postRemoveHosts {
		if strings.Contains(h, toRemove) {
			removed = false
		}
	}
	if !removed {
		t.Fatalf("expected host %s to be removed", toRemove)
	}
	if len(initialHosts) != len(postRemoveHosts)+1 {
		t.Fatalf("host count mismatch after removal")
	}
	if len(initialAvail) != len(postRemoveAvail)+1 {
		t.Fatalf("available slice length mismatch after removal")
	}

	// AddHost requires traversal source
	lb.AddHost(toRemove, "g")

	postAddHosts := lb.GetClients()
	postAddAvail := lb.GetAvailable()

	added := false
	for _, h := range postAddHosts {
		if strings.Contains(h, toRemove) {
			added = true
		}
	}
	if !added {
		t.Fatalf("expected host %s to be re-added", toRemove)
	}
	if len(postRemoveHosts) != len(postAddHosts)-1 {
		t.Fatalf("host count mismatch after add")
	}
	if len(postRemoveAvail) != len(postAddAvail)-1 {
		t.Fatalf("available slice length mismatch after add")
	}
}

func TestRotation(t *testing.T) {
	buf := &bytes.Buffer{}
	logger := newLogger(buf)
	lb := loadbalancer.NewRoundRobinClientRemoteConnection(endpoints, "g", 2*time.Second, logger)
	defer lb.Close()

	setupGraph(t, lb)
	buf.Reset() // clear seed logs so we count only the loop below

	// 5 traversals; expect distribution 0,1,2,0,1
	for i := 1; i <= 5; i++ {
		_, err := lb.DoList(func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error) {
			// We don't care about results here, only that a traversal was submitted
			return g.V().Has("name", "Alice").Limit(int64(i)).ToList()
		})
		if err != nil {
			t.Fatalf("ToList error: %v", err)
		}
	}

	logs := buf.String()
	if strings.Count(logs, "Traversal submitted via connection #0") != 2 {
		t.Fatalf("expected 2 via #0\n%s", logs)
	}
	if strings.Count(logs, "Traversal submitted via connection #1") != 2 {
		t.Fatalf("expected 2 via #1\n%s", logs)
	}
	if strings.Count(logs, "Traversal submitted via connection #2") != 1 {
		t.Fatalf("expected 1 via #2\n%s", logs)
	}
}

func TestHealthCheck(t *testing.T) {
	buf := &bytes.Buffer{}
	logger := newLogger(buf)
	lb := loadbalancer.NewRoundRobinClientRemoteConnection(endpoints, "g", 2*time.Second, logger)
	defer lb.Close()

	setupGraph(t, lb)

	// Compose names/ports: gremlin1->8181, gremlin2->8182, gremlin3->8183
	const containerName = "aerospike-graph-service-2"
	hostEndpoint := endpoints[1] // "localhost:8182"

	if err := stopContainerAndWait(containerName, hostEndpoint, 25*time.Second); err != nil {
		t.Skipf("could not stop %s: %v", containerName, err)
	}
	defer startContainerAndWait(containerName, hostEndpoint, 30*time.Second) // best-effort restore

	// Trigger some traffic so the LB lands on the down host and marks it unhealthy
	for i := 0; i < 3; i++ {
		_, _ = lb.DoList(func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error) {
			return g.V().Limit(5).ToList()
		})
		time.Sleep(200 * time.Millisecond)
	}

	// Give health loop time to observe and/or probe
	time.Sleep(3 * time.Second)

	// Expect at least one host unhealthy
	avail := lb.GetAvailable()
	foundUnhealthy := false
	for _, ok := range avail {
		if !ok {
			foundUnhealthy = true
			break
		}
	}
	if !foundUnhealthy {
		t.Fatalf("expected at least one host to be unhealthy")
	}

	// Start it again and wait for healthcheck to revive it
	if err := startContainerAndWait(containerName, hostEndpoint, 30*time.Second); err != nil {
		t.Fatalf("failed to restart container: %v", err)
	}
	// Health loop runs every 2s (per constructor); give it some time
	time.Sleep(5 * time.Second)

	avail2 := lb.GetAvailable()
	for i, ok := range avail2 {
		if !ok {
			t.Fatalf("expected all hosts healthy after restart; host %d still down", i)
		}
	}
}

// --- Docker CLI helpers + port waiters ---

func dockerCmd(args ...string) error {
	cmd := exec.Command("docker", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("docker %v: %v\n%s", args, err, string(out))
	}
	return nil
}

func stopContainerAndWait(containerName, hostEndpoint string, timeout time.Duration) error {
	if err := dockerCmd("stop", containerName); err != nil {
		return err
	}
	return waitPortClosed(hostEndpoint, timeout)
}

func startContainerAndWait(containerName, hostEndpoint string, timeout time.Duration) error {
	if err := dockerCmd("start", containerName); err != nil {
		return err
	}
	return waitPortOpen(hostEndpoint, timeout)
}

func waitPortOpen(addr string, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for {
		conn, err := net.DialTimeout("tcp", addr, 600*time.Millisecond)
		if err == nil {
			_ = conn.Close()
			return nil
		}
		if time.Now().After(deadline) {
			return fmt.Errorf("port %s did not open within %s: %w", addr, timeout, err)
		}
		time.Sleep(300 * time.Millisecond)
	}
}

func waitPortClosed(addr string, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for {
		conn, err := net.DialTimeout("tcp", addr, 600*time.Millisecond)
		if err != nil {
			// connection refused / no route -> closed
			return nil
		}
		_ = conn.Close()
		if time.Now().After(deadline) {
			return errors.New("port " + addr + " still open after " + timeout.String())
		}
		time.Sleep(300 * time.Millisecond)
	}
}
