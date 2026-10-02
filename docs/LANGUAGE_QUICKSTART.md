# Language quickstart

## Python
`pip install -e packages/python` then import `agent_ledger`. The Python package is the reference runtime and includes file durability, SQLite WAL state, DB-API production database seams, content-addressed local blobs, and S3/MinIO-compatible blobs.

## TypeScript
`cd packages/typescript && npm install && npm test`. TypeScript implements runtime/effect/JCS/Merkle/replay semantics plus storage and framework adapter contracts.

## Go
`cd go && go run ./cmd/agentledger-go conformance ../contracts/conformance/runtime_semantics.v1.json`. Go provides native run/fencing and effect-transition semantics.

## Rust
`cd rust && cargo run -- conformance ../contracts/conformance/runtime_semantics.v1.json`. Rust provides native run/fencing and effect-transition semantics.

The shared source of truth is `contracts/agentledger.runtime.v1.json`; behavioral fixtures are under `contracts/conformance/`.
