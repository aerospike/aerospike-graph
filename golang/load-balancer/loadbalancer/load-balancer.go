package loadbalancer

import (
	"context"
	"errors"
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"

	gremlingo "github.com/apache/tinkerpop/gremlin-go/v3/driver"
)

var ErrNoHealthyHosts = errors.New("no healthy Gremlin hosts available")

type rrEntry struct {
	conn    *gremlingo.DriverRemoteConnection
	address string
}

type RoundRobinClientRemoteConnection struct {
	logger      *log.Logger
	pos         uint64
	healthEvery time.Duration

	mu        sync.Mutex
	entries   []*rrEntry
	available []atomic.Bool

	stopCh chan struct{}
	wg     sync.WaitGroup
}

func NewRoundRobinClientRemoteConnection(endpoints []string, traversalSource string, healthCheckInterval time.Duration, logger *log.Logger) *RoundRobinClientRemoteConnection {
	if logger == nil {
		logger = log.Default()
	}
	lb := &RoundRobinClientRemoteConnection{
		logger:      logger,
		healthEvery: healthCheckInterval,
		stopCh:      make(chan struct{}),
	}
	for _, ep := range endpoints {
		ws := fmt.Sprintf("ws://%s/gremlin", ep)
		drc, err := gremlingo.NewDriverRemoteConnection(ws, func(s *gremlingo.DriverRemoteConnectionSettings) {
			s.TraversalSource = traversalSource
		})
		if err != nil {
			lb.logger.Printf("Failed to open %s: %v (marking down)", ws, err)
			lb.entries = append(lb.entries, &rrEntry{conn: nil, address: ws})
			var b atomic.Bool
			b.Store(false)
			lb.available = append(lb.available, b)
			continue
		}
		lb.entries = append(lb.entries, &rrEntry{conn: drc, address: ws})
		var b atomic.Bool
		b.Store(true)
		lb.available = append(lb.available, b)
	}
	lb.wg.Add(1)
	go lb.healthLoop(traversalSource)
	lb.logger.Printf("Initialized load-balancer with endpoints: %v", endpoints)
	return lb
}

func (lb *RoundRobinClientRemoteConnection) Close() {
	close(lb.stopCh)
	lb.wg.Wait()
	lb.mu.Lock()
	defer lb.mu.Unlock()
	for _, e := range lb.entries {
		if e.conn != nil {
			e.conn.Close()
		}
	}
	lb.logger.Printf("Load-balancer shut down")
}

func (lb *RoundRobinClientRemoteConnection) AddHost(endpoint, traversalSource string) {
	ws := fmt.Sprintf("ws://%s/gremlin", endpoint)
	drc, err := gremlingo.NewDriverRemoteConnection(ws, func(s *gremlingo.DriverRemoteConnectionSettings) {
		s.TraversalSource = traversalSource
	})
	lb.mu.Lock()
	defer lb.mu.Unlock()
	var b atomic.Bool
	if err != nil {
		lb.logger.Printf("AddHost failed to open %s: %v (marking down)", ws, err)
		b.Store(false)
		lb.entries = append(lb.entries, &rrEntry{conn: nil, address: ws})
	} else {
		b.Store(true)
		lb.entries = append(lb.entries, &rrEntry{conn: drc, address: ws})
	}
	lb.available = append(lb.available, b)
	lb.logger.Printf("Added host %s", endpoint)
}

func (lb *RoundRobinClientRemoteConnection) RemoveHost(endpoint string) {
	ws := fmt.Sprintf("ws://%s/gremlin", endpoint)
	lb.mu.Lock()
	defer lb.mu.Unlock()

	idx := -1
	for i, e := range lb.entries {
		if e.address == ws {
			idx = i
			break
		}
	}
	if idx < 0 {
		lb.logger.Printf("Tried to remove non-existent host %s", endpoint)
		return
	}
	if lb.entries[idx].conn != nil {
		lb.entries[idx].conn.Close()
	}
	lb.entries = append(lb.entries[:idx], lb.entries[idx+1:]...)
	lb.available = append(lb.available[:idx], lb.available[idx+1:]...)
	lb.logger.Printf("Removed host %s", endpoint)
}

func (lb *RoundRobinClientRemoteConnection) healthyIndexes() []int {
	out := make([]int, 0, len(lb.entries))
	for i := range lb.entries {
		if lb.available[i].Load() && lb.entries[i].conn != nil {
			out = append(out, i)
		}
	}
	return out
}

func (lb *RoundRobinClientRemoteConnection) WithRemote() (*gremlingo.GraphTraversalSource, int, error) {
	lb.mu.Lock()
	defer lb.mu.Unlock()

	healthy := lb.healthyIndexes()
	if len(healthy) == 0 {
		return nil, -1, ErrNoHealthyHosts
	}
	pos := int(atomic.AddUint64(&lb.pos, 1)-1) % len(healthy)
	idx := healthy[pos]
	conn := lb.entries[idx].conn

	lb.logger.Printf("Traversal submitted via connection #%d", idx)
	g := gremlingo.Traversal_().WithRemote(conn)
	return g, idx, nil
}

func (lb *RoundRobinClientRemoteConnection) DoIter(
	f func(g *gremlingo.GraphTraversalSource) <-chan error,
) error {
	g, idx, err := lb.WithRemote()
	if err != nil {
		return err
	}

	errCh := f(g)
	var firstErr error
	for e := range errCh {
		if e != nil && firstErr == nil {
			firstErr = e
		}
	}

	if firstErr != nil {
		lb.available[idx].Store(false)
		lb.logger.Printf("Connection #%d failed during Iterate(): %v – marking host down", idx, firstErr)
		return firstErr
	}
	return nil
}

func (lb *RoundRobinClientRemoteConnection) DoList(
	f func(g *gremlingo.GraphTraversalSource) ([]*gremlingo.Result, error),
) ([]*gremlingo.Result, error) {
	g, idx, err := lb.WithRemote()
	if err != nil {
		return nil, err
	}
	rows, err := f(g)
	if err != nil {
		lb.available[idx].Store(false)
		lb.logger.Printf("Connection #%d failed: %v – marking host down", idx, err)
		return nil, err
	}
	return rows, nil
}

func (lb *RoundRobinClientRemoteConnection) healthLoop(traversalSource string) {
	defer lb.wg.Done()
	t := time.NewTicker(lb.healthEvery)
	defer t.Stop()
	for {
		select {
		case <-lb.stopCh:
			return
		case <-t.C:
			lb.logger.Printf("Running health check")
			lb.mu.Lock()
			entries := lb.entries
			lb.mu.Unlock()

			for i := range entries {
				if entries[i].conn == nil {
					drc, err := gremlingo.NewDriverRemoteConnection(entries[i].address, func(s *gremlingo.DriverRemoteConnectionSettings) {
						s.TraversalSource = traversalSource
					})
					if err != nil {
						lb.available[i].Store(false)
						lb.logger.Printf("Host #%d reopen failed: %v", i, err)
						continue
					}
					lb.mu.Lock()
					entries[i].conn = drc
					lb.mu.Unlock()
				}

				_, cancel := context.WithTimeout(context.Background(), 3*time.Second)
				g := gremlingo.Traversal_().WithRemote(entries[i].conn)
				_, err := g.V().Limit(1).ToList()
				cancel()

				if err == nil {
					lb.available[i].Store(true)
					lb.logger.Printf("Host #%d is healthy", i)
				} else {
					lb.available[i].Store(false)
					lb.logger.Printf("Host #%d still down", i)
				}
			}
		}
	}
}

func (lb *RoundRobinClientRemoteConnection) GetClients() []string {
	lb.mu.Lock()
	defer lb.mu.Unlock()
	out := make([]string, len(lb.entries))
	for i, e := range lb.entries {
		out[i] = e.address
	}
	return out
}

func (lb *RoundRobinClientRemoteConnection) GetAvailable() []bool {
	lb.mu.Lock()
	defer lb.mu.Unlock()
	out := make([]bool, len(lb.available))
	for i := range lb.available {
		out[i] = lb.available[i].Load()
	}
	return out
}

func (lb *RoundRobinClientRemoteConnection) SetNextIndex(i int) {
	atomic.StoreUint64(&lb.pos, uint64(i))
}
