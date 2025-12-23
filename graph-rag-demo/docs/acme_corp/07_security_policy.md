# Security Policy SP-001: Data Protection Standards

**Owner:** David Kim (Head of Security)
**Effective Date:** January 1, 2023
**Last Review:** September 2024
**Status:** Active

## Purpose

This policy establishes data protection standards for all Acme Corp products: NexusDB, GraphSync, and QueryStudio.

## Scope

Applies to all engineering teams: Platform Team, Infrastructure Team, Product Team, and Security Team.

## Requirements

### 1. Encryption Standards

- **Data at Rest:** AES-256 encryption required for all customer data
- **Data in Transit:** TLS 1.3 minimum for all external connections
- **Key Management:** All keys stored in HashiCorp Vault

### 2. Access Control

- Role-Based Access Control (RBAC) enforced on all systems
- Principle of least privilege for service accounts
- Quarterly access reviews by team leads

### 3. Security Reviews

All new features require Security Review (SR) before production:
- SR approval from Security Team required
- Review must cover: authentication, authorization, data handling, logging

Recent reviews:
- SR-2023-015: GraphSync bidirectional sync (approved with conditions)
- SR-2024-001: QueryStudio public sharing feature (pending)

### 4. Incident Response

- All security incidents reported to David Kim within 1 hour
- P1 incidents require executive notification (Sarah Chen, Marcus Williams)
- Post-incident review within 5 business days

### 5. Compliance

- SOC2 Type II certification maintained
- Annual penetration testing by third party
- Vulnerability scanning weekly (managed by Alex Chen's team)

## Exceptions

Exceptions require written approval from:
- David Kim (Head of Security) for P3/P4 items
- Sarah Chen (CEO) for P1/P2 items

## Related Documents

- NexusDB Product Spec (security section)
- GraphSync Product Spec (security section)
- Incident Response Playbook
- SOC2 Evidence Repository

