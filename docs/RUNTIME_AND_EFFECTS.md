# Durable runtime and external effects (v0.5)

AgentLedger distinguishes **execution progress** from **external side effects**.

`DurableRunStore` persists run status, step checkpoints, revisions, and fencing tokens. A newly acquired lease invalidates an older worker's token, preventing a stale worker from committing a checkpoint after recovery.

`EffectLedger` records consequential writes using an explicit lifecycle:

`PROPOSED → AUTHORIZED → ATTEMPTED → COMMITTED | FAILED | UNKNOWN`

`UNKNOWN` is intentional. If a process loses contact with an external service after sending a request, AgentLedger does not assume either success or failure. A reconciliation step must resolve the effect to `COMMITTED` or `FAILED`. Idempotency keys are bound to request hashes and cannot be reused for a different request.

The optional `crypto` Python extra adds Ed25519 signatures and public-key fingerprints for evidence. Existing SHA-256 chain verification remains supported. Signatures currently use AgentLedger's deterministic sorted-JSON representation; this is deliberately labeled `sorted-json-v1`, not RFC 8785/JCS.

These primitives are local SDK building blocks. They do not by themselves provide distributed consensus, exactly-once delivery, or proof that an external system performed an effect.
