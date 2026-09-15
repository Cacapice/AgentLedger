# Agent Ledger

**A tamper-evident accountability layer for autonomous AI agents.**

[![Python tests](https://github.com/Cacapice/AgentLedger/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Cacapice/AgentLedger/actions/workflows/python-tests.yml)

Agent Ledger records consequential agent actions with attribution, authority, policy context, results, and verifiable audit evidence. It is designed to support operational governance and audit evidence without replacing the developer's existing agent framework or observability stack.

## Agent Safety & Python Developer Experience

The Python SDK now includes validated Pydantic transaction records and agent-specific financial guardrails:

```python
from agent_ledger import Ledger

ledger = Ledger(balances={"agent_a": 100, "agent_b": 0}, strict=True)

with ledger.transaction():
    ledger.debit("agent_a", 50, idempotency_key="purchase_123")
    ledger.credit("agent_b", 50)

ledger.transfer("agent_a", "agent_b", 10, allow_negative=False)
df = ledger.get_history()  # pip install 'agent-ledger[analytics]'
```

- **Atomic transactions:** context-manager rollback if a block fails.
- **Strict mode:** overdraft protection by default.
- **Idempotency keys:** safe retries without duplicate debits/transfers.
- **Pydantic models:** validated, typed transaction records.
- **Structured JSON logs:** transaction events are emitted through Python logging.
- **Pandas/CSV export:** notebook-friendly transaction history.
- **Budget decorator:** `@ledger.limit_spending(max_cost=5.00)` rolls back work that exceeds the configured cap.
- **Scenario example:** `examples/agent_marketplace.py` demonstrates atomic agent-to-agent settlement.

## v4.4.1 — Self-Service Launch Control Plane

v4.4.1 introduced the self-service commercial control plane for hosted Agent Ledger deployments.

Key updates:

- Self-service user signup and login.
- Automatic tenant provisioning.
- Role-based access control for owner, admin, auditor, developer, and billing roles.
- API-key lifecycle management and machine scopes.
- Usage and account console.
- Agent and policy inventory.
- Audit search and evidence export.
- Retention automation.
- External signing and anchoring hooks.
- Billing entitlement support and Stripe-compatible webhook handling.
- Release and deployment automation.

Agent Ledger supports audit and control evidence; deployment does not itself constitute certification or regulatory compliance.

## Commercial tiers — reference

| Tier | Monthly price | Included events / month |
| --- | ---: | ---: |
| Developer | Free | 25,000 |
| Starter | $20 | 50,000 |
| Pro | $49 | 250,000 |
| Governance | $99 | 1,000,000 |
| Scale | $249 | 5,000,000 |
| Enterprise | Custom | Custom |

Usage notifications begin before the monthly event limit is reached. Entitlements and ingestion limits are enforced by the hosted control plane.

## Project boundary

Developer-facing SDKs, schemas, integrations, examples, and MCP tooling are intended for public distribution. The hosted ingestion service, tenant control plane, billing internals, payment reconciliation, credentials, and production infrastructure configuration should remain private.

## Documentation

Deployment and publishing guidance is available in:

- `docs/DEPLOYMENT.md`
- `docs/PUBLISHING.md`
- `docs/API.md`


## Testing standard

CI runs the Python suite across Python 3.10–3.13 with coverage reporting on every push and pull request. The current repository-wide baseline is enforced in CI and should be ratcheted upward as legacy modules gain tests; the target for money-moving balance primitives is 100% behavioral coverage, including rollback, overdraft, retry/idempotency, transfer, analytics export, and spending-limit paths.
