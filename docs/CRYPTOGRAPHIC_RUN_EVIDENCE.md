# Cryptographic run evidence

AgentLedger uses RFC 8785 JCS bytes as the cryptographic representation of JSON evidence. JCS inputs are constrained to I-JSON: non-finite numbers and lone surrogates are rejected; Python also rejects integers outside the exact binary64 range and recommends encoding them as strings.

Run manifests commit independently to ordered event and effect sequences. Leaves are `SHA-256(0x00 || JCS(value))`; internal nodes are `SHA-256(0x01 || left || right)`. An odd node is duplicated. Empty trees use `SHA-256("")`. The manifest can be signed with Ed25519 and includes the key fingerprint.

Replay is non-effecting by default. `replay_compare` compares canonical evidence. Python `replay_effects` executes only when an executor is explicitly supplied. An `UNKNOWN` effect must be reconciled to `COMMITTED` or `FAILED`; it must not be blindly retried.

MCP tools expose run creation/acquisition/checkpointing, effect proposal/transitions, manifest construction, and replay comparison. IDs and fencing tokens are explicit request inputs; callers must not infer run/session identity from an MCP transport connection.
