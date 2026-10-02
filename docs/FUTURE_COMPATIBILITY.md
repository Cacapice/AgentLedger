# Future compatibility and transition contract

AgentLedger treats persisted evidence as a long-lived interface. New runtimes must not silently reinterpret old evidence.

## Rules

1. Evidence bundles, manifests, runtime contracts, and canonicalization algorithms carry explicit identifiers.
2. Readers reject unknown major formats rather than guessing.
3. New fields are additive within a major version; semantic changes require a new version and migration fixture.
4. Signatures are always verified over the original version's canonical bytes. Migration creates a new derived artifact and never rewrites signed history.
5. Adapter capability discovery is machine-readable (`agent_ledger.compat.capabilities`).
6. Cross-language parity is claimed only after shared fixtures pass in CI.
7. Side effects remain non-replayable by default; UNKNOWN outcomes require provider reconciliation.

## Transition path

`v0.x evidence -> verify original -> normalize to internal model -> optionally derive newer bundle -> preserve source hash/signature -> record migration provenance`.

This makes future v1/v2 storage and API changes possible without invalidating old evidence.
