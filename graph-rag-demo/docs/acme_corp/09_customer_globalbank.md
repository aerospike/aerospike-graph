# Customer Profile: GlobalBank Corp

**Account Owner:** Lisa Park (VP Product)
**Technical Contact:** Alex Chen (Infrastructure Team)
**Contract Value:** $2.4M ARR
**Customer Since:** 2021

## Deployment Overview

GlobalBank Corp uses Acme products for their fraud detection platform:

- **NexusDB Enterprise** - 12-node cluster across 3 regions
- **GraphSync Professional** - Syncing from 4 PostgreSQL databases
- **QueryStudio Team** - 50 analyst seats

## Use Case

Real-time fraud detection using transaction graph analysis:
- 500M+ transaction edges
- 50M+ customer nodes
- Sub-100ms query latency requirement

## Technical Architecture

- Deployed on AWS (us-east-1, us-west-2, eu-west-1)
- Managed by GlobalBank's DevOps team with support from Alex Chen
- Custom integration built by Michael Brown's Product Team

## Support History

### Incidents
- INC-2024-003 (P1): GraphSync data inconsistency - Resolved
- INC-2023-012 (P3): Query timeout during peak hours - Resolved

### Feature Requests
- FR-2024-001: Multi-tenancy support (scheduled for 2025)
- FR-2024-002: Real-time alerting integration (in GSYNC-501)

## Relationship Notes

- Key stakeholder: Maria Santos (GlobalBank VP Engineering)
- Quarterly business review with Sarah Chen
- Considering expansion to additional business units

## Contract Details

- Enterprise SLA: 99.95% uptime
- 24/7 support with 15-minute P1 response
- Annual renewal: March 2025

