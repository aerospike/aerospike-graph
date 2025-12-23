# Engineering All-Hands Meeting Notes

**Date:** October 15, 2024
**Attendees:** James Rodriguez (host), all engineering team leads
**Location:** Austin HQ + Zoom

## Agenda

1. Q3 retrospective
2. Q4 roadmap review
3. Incident review
4. Team updates
5. Open discussion

## Q3 Retrospective

**James Rodriguez:** Overall strong quarter. Shipped GraphSync 2.4.0 and QueryStudio 1.2.0.

Highlights:
- NexusDB query performance improved 40% (Emily Watson's team)
- Zero P1 incidents in September (best month ever)
- HealthData Inc deployment successful

Lowlights:
- INC-2024-003 at GlobalBank was painful
- NEXUS-1542 still not fixed (Emily taking this in Q4)

## Q4 Roadmap Review

**Lisa Park:** Reviewed Q4 priorities (see Q4 Roadmap document)

Key discussion points:
- Emily Watson raised concern about NEXUS-2000 timeline given NEXUS-1542
- David Kim flagged SR-2024-001 may need additional review time
- Alex Chen confirmed multi-cloud support is on track

## Incident Review

**Alex Chen:** Reviewed INC-2024-007 lessons learned

Action items:
- Better capacity planning process needed
- Rachel Green to create customer sizing guide
- Consider per-customer resource quotas

## Team Updates

### Platform Team (Emily Watson)
- Nina Patel's query planner v2 ahead of schedule
- Tom Harris compression work showing 30% storage reduction
- Hiring: Looking for senior distributed systems engineer

### Infrastructure Team (Alex Chen)
- Kubernetes 1.28 upgrade complete
- Cost savings: 15% reduction in cloud spend
- Rachel Green promoted to Senior SRE

### Product Team (Michael Brown)
- GraphSync HA mode design complete
- Jennifer Liu demoing QueryStudio sharing next week
- Daniel Kim onboarded new engineer (starting Nov 1)

### Security Team (David Kim)
- SOC2 audit scheduled for November
- Penetration test results: 2 medium findings, being addressed
- Security Review SR-2024-001 in progress

## Action Items

| Item | Owner | Due Date |
|------|-------|----------|
| Fix NEXUS-1542 | Emily Watson | Oct 31 |
| Complete SR-2024-001 | David Kim | Oct 25 |
| Customer sizing guide | Rachel Green | Nov 15 |
| Hiring plan for Platform | Emily Watson | Oct 20 |

## Next Meeting

November 12, 2024 - Q4 mid-quarter review

