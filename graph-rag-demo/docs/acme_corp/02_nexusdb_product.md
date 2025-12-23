# NexusDB - Product Specification

**Product Owner:** Lisa Park (VP Product)
**Engineering Lead:** Emily Watson (Platform Team)
**Version:** 3.2.1 (Released Q2 2024)

## Overview

NexusDB is Acme Corp's flagship distributed graph database. It handles billions of edges with sub-millisecond query latency.

## Architecture

- **Storage Layer:** Custom LSM-tree implementation by Alex Chen's Infrastructure Team
- **Query Engine:** Gremlin-compatible, developed by Platform Team
- **Replication:** Multi-region active-active, designed by Marcus Williams

## Key Features

1. **Graph Sharding** - Automatic partitioning across nodes
2. **ACID Transactions** - Full transactional support (added in v2.0)
3. **Time Travel Queries** - Historical graph state queries (added in v3.0)

## Security

- All data encrypted at rest (AES-256)
- TLS 1.3 for data in transit
- RBAC managed by Security Team under David Kim
- SOC2 Type II certified (see Security Policy SP-001)

## Known Issues

- NEXUS-1542: Memory leak in time travel queries (assigned to Emily Watson)
- NEXUS-1589: Slow replication under high write load (Infrastructure Team investigating)

## Dependencies

- Requires GraphSync v2.0+ for real-time sync features
- Integrates with QueryStudio for visualization

