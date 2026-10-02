# Verifiable Operations

The release claim is backed by six concrete capabilities:

1. Portable `.alb` Evidence Bundles with offline manifest/signature/root verification.
2. Signed-root selective disclosure using Merkle inclusion proofs.
3. Read-only provider-specific reconciliation for ambiguous `UNKNOWN` effects:
   Stripe PaymentIntents, GitHub operation lookup, and generic idempotency-query APIs.
4. Optional OpenTelemetry/W3C context injection/extraction and AgentLedger causal span attributes.
5. Side-effect-free historical policy simulation.
6. Evidence-derived SLO scorecards, including objective thresholds and per-agent/version/provider grouping.

## Safety boundary

Reconcilers query provider truth. They never repeat the original mutation. An unresolved lookup
remains `UNKNOWN`.

## Selective disclosure

A disclosure packet contains only the selected evidence value, its inclusion proof, and the signed
manifest. Verification checks the leaf, Merkle path, signed root, and (when present) Ed25519
signature. Redaction of fields inside a committed leaf is not possible without invalidating the
proof; privacy-sensitive fields should therefore be committed separately or represented by
pre-committed hashes.

## OTEL

`agent_ledger.otel` uses the installed OpenTelemetry API propagator rather than implementing
`traceparent` itself. This preserves compatibility with configured W3C/baggage propagators.
AgentLedger evidence remains the authoritative verifiable record; traces are correlation/operations
data.

## SLO scorecards

`scorecard()` evaluates committed, unknown, failed and replay-divergence objectives and returns
machine-readable actual/target/met values plus a normalized objective score. `grouped_scorecards()`
supports per-agent, version and provider views.
