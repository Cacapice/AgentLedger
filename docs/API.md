# Hosted API

All `/v1/*` calls require `Authorization: Bearer <tenant-api-key>`.

## POST /v1/events

Required body fields: `agent_id`, `action_type`, `tool_name`, `execution_status`.

Optional header: `Idempotency-Key`.

Response `202`:

```json
{"accepted":true,"server_event_id":"...","chain_id":"...","sequence_number":42,"event_hash":"...","received_at":"..."}
```

## POST /v1/events/batch

Body: `{"events":[...]}`. Maximum batch defaults to 100.

## GET /v1/usage

Returns plan, retention, monthly limit, totals, and hourly buckets. Optional `from=<ISO timestamp>` query parameter.

## GET /healthz

Unauthenticated liveness endpoint.
