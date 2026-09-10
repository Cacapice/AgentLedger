# Agent Operations

Agent Ledger turns the same consequential-action evidence used for receipts into an operational view. `agent-ledger doctor --production` summarizes fleet health, action success, repeated-action loops, failure clusters, and version regressions over the last seven days by default.

```bash
agent-ledger doctor --production
agent-ledger doctor --production --days 14
agent-ledger doctor --production --json
```

The hosted endpoint is `GET /v1/operations/health?days=7` and requires `audit:read`.

## Detection semantics
- Health is a deterministic 0–100 operational indicator derived from failures, policy blocks, and detected loops. It is not an SLA or security score.
- Loop detection flags 3+ identical agent/action/tool/input events separated by no more than 60 seconds.
- Version regression requires at least five observed events in each of two versions and flags a success-rate decline greater than five percentage points.
- Failure clustering groups failed actions by structured error code/type/message when available.
- The endpoint analyzes at most 10,000 events per request and reports `window.truncated=true` when that ceiling is reached.
