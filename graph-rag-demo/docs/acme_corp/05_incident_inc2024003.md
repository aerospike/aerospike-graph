# Incident Report: INC-2024-003

**Severity:** P1 (Critical)
**Status:** Resolved
**Date:** March 15, 2024
**Duration:** 4 hours 23 minutes

## Summary

GraphSync caused data inconsistency at GlobalBank Corp, resulting in duplicate transaction records in their NexusDB instance.

## Timeline

- **09:15 UTC** - GlobalBank Corp reports duplicate records in fraud detection graph
- **09:22 UTC** - On-call engineer (Alex Chen) paged
- **09:45 UTC** - Root cause identified: GraphSync race condition in bidirectional sync
- **10:30 UTC** - Michael Brown (GraphSync lead) joins incident
- **11:00 UTC** - Hotfix deployed to GlobalBank Corp environment
- **13:38 UTC** - Data reconciliation complete, incident resolved

## Root Cause

Race condition in GraphSync's conflict resolution logic when processing high-volume bidirectional syncs. The bug was introduced in GraphSync v2.2.0.

## Impact

- 15,000 duplicate transaction edges created
- GlobalBank Corp's fraud detection alerts were 2x false positive rate
- Customer trust impact: Medium

## Resolution

- Hotfix: Added distributed lock for conflict resolution (deployed v2.2.1)
- Data cleanup: Manual deduplication by Infrastructure Team

## Action Items

1. Add integration test for high-volume bidirectional sync - Michael Brown - Done
2. Improve conflict resolution documentation - Jennifer Liu - Done
3. Review similar patterns in NexusDB replication - Emily Watson - In Progress
4. Update Security Review SR-2023-015 with new findings - David Kim - Done

## Related Documents

- GraphSync Product Spec
- Security Review SR-2023-015
- GlobalBank Corp SLA Agreement

