# Production adapter certification

AgentLedger v0.8 treats adapters as claims that must be tested, not names in a compatibility table.

## Real-service gate

`integration-certification.yml` boots PostgreSQL 16, MySQL 8.4 and MinIO, then runs the same StateStore/BlobStore certification used locally. `docker-compose.integration.yml` provides the same stack for maintainers.

## Failure-injection gate

`agent_ledger.certification` supplies deterministic wrappers/checks for stale compare-and-swap, transient state-store failure and corrupt blob reads. The distributed lease suite additionally proves exclusivity, heartbeat renewal, expiry takeover and monotonically increasing fencing tokens.

A production adapter should not be advertised as certified unless its real service and failure suite passes in CI.

## Distributed lease contract

`DistributedLeaseManager` is backed by revisioned StateStore CAS. Each takeover increments a fencing token. Heartbeats extend TTL only for the current owner/token/fence. Consumers protecting an external resource should persist or compare the fencing value at that resource boundary; TTL alone cannot stop a paused stale worker.

## Safety boundary

Fault injection never calls arbitrary external production tools. Framework examples use the normal effect ledger, where ambiguous writes become `UNKNOWN` and require reconciliation.
