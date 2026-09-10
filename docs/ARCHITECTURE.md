# Architecture

```text
Agent / App
   |  Python SDK / TypeScript SDK / MCP
   v
Tenant-scoped HTTPS Ingestion API
   |-- authenticate API key (hashed at rest)
   |-- validate + bound payload
   |-- preserve source-chain references
   |-- assign server event id / sequence
   |-- extend tenant hash chain
   |-- increment hourly usage counters
   v
D1
   |-- tenants
   |-- api_keys
   |-- audit_events
   |-- audit_chain_heads
   |-- usage_hourly
```

The local SDK chain and hosted chain are intentionally distinct. The hosted service stores source-chain identifiers/hashes as provenance while creating a server-controlled tenant chain. This prevents a client from choosing the server chain head and provides an independently verifiable receipt boundary.

## Trust boundaries

1. SDK boundary: redact/minimize before transport.
2. Authentication boundary: every hosted request maps to one tenant and authorized scope.
3. Ledger boundary: the service assigns server event IDs, sequence numbers and event hashes.
4. Meter boundary: accepted events increment counters in the same D1 batch as the event write.

The prototype uses D1 atomic batches. High-assurance enterprise deployments should additionally anchor chain heads externally (for example object-lock storage, KMS signatures, or a transparency service) and use a serialized per-tenant writer to eliminate concurrent head races at high throughput.
