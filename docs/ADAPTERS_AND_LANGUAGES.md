# Adapters and language runtimes

AgentLedger is contract-first. Python is the reference implementation; TypeScript is a full SDK/runtime surface; Go and Rust provide native runtime-core baselines. All languages consume `contracts/conformance/runtime_semantics.v1.json` and must preserve fencing, effect-transition, idempotency, UNKNOWN/reconciliation, and non-effecting replay semantics.

## Storage
- Python: file runtime, SQLite WAL `StateStore`, generic DB-API Postgres/MySQL seam.
- Blob evidence: local content-addressed storage and an S3/MinIO-compatible adapter.
- TypeScript: `StateStore` and `BlobStore` contracts with a dependency-free memory implementation; production drivers can live outside core.

## Framework adapters
Dependency-free facades are supplied for LangGraph, LangChain, CrewAI, AutoGen, OpenAI Agents SDK, LlamaIndex, and Semantic Kernel. These are runtime-boundary adapters, not replacements for framework planning or graph execution.

## Certification rule
An adapter or language should not be described as production-ready merely because it compiles. It should pass shared semantic fixtures plus backend-specific crash/recovery and integration tests. Optional production dependencies remain outside the core package.
