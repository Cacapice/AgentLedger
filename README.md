# Agent Ledger

**The system of record for consequential autonomous-agent actions.** Observability tells you what ran; Agent Ledger records who/what/authority/policy/result and returns a tamper-evident receipt.

```bash
pip install agent-ledger
agent-ledger init
agent-ledger doctor
agent-ledger verify alr_YOUR_RECEIPT
```

See `docs/DEVELOPER_ADOPTION.md`, `docs/ACCOUNTABILITY_MODEL.md`, and `integrations/`.

## Canonical five-minute dogfood demo

Run one real, read-only Scuderia agent action and receive a hosted `alr_...` receipt:

```bash
python -m pip install -e packages/python
agent-ledger init --url https://YOUR-WORKER.workers.dev --api-key al_YOUR_KEY
agent-ledger doctor
agent-ledger dogfood-scuderia
```

Then independently verify the exact receipt returned by the Worker:

```bash
agent-ledger verify alr_<receipt-id>
```

See `docs/FIVE_MINUTE_QUICKSTART.md` and `docs/PUBLIC_DEMO.md`. The demo makes a read-only GET to a Scuderia-owned public page; it does not mutate the site or Search Console.

# Agent Ledger

Agent Ledger is a tamper-evident system of record for consequential autonomous-agent actions.

This distributable package separates reusable agent accountability infrastructure from the Scuderia reference deployment. It provides:

- Python SDK (`agent-ledger`) with decorators, redaction, local JSONL chains, hosted ingestion client, and CLI verification.
- TypeScript SDK (`@agent-ledger/sdk`) for Node, browser/edge runtimes, and framework adapters.
- MCP server (`@agent-ledger/mcp`) exposing `audit_record`, `audit_verify_file`, and `audit_usage` tools.
- Cloudflare Workers hosted ingestion API with per-tenant API keys, chain heads, idempotency, and usage metering.
- D1 tenant/metering schema.
- Minimal static developer site.
- Explicit open-source/commercial license boundary.

## Product boundary

`packages/` and `apps/mcp/` are Apache-2.0 licensed developer-distribution components. `services/ingestion/` is commercial control-plane source and is governed by `LICENSE-COMMERCIAL.md`. The example developer site is Apache-2.0 and may be deployed independently.

## Quick start

### Python

```bash
cd packages/python
python -m pip install -e .
agent-ledger verify ./audit_events.jsonl
```

```python
from agent_ledger import AuditLogger, audit_tool

logger = AuditLogger.from_env()

@audit_tool(agent_id="finance-agent", logger=logger)
def create_payment(amount: float, recipient_account: str):
    return {"status": "queued", "amount": amount}
```

### TypeScript

```bash
cd packages/typescript
npm install
npm run build
```

```ts
import { AuditClient } from "@agent-ledger/sdk";
const ledger = new AuditClient({ baseUrl: process.env.AGENT_LEDGER_URL!, apiKey: process.env.AGENT_LEDGER_API_KEY! });
await ledger.record({ agent_id: "research-agent", action_type: "TOOL_CALL", tool_name: "web.search", execution_status: "SUCCESS", input_parameters: { q: "example" } });
```

### MCP

```bash
cd apps/mcp
npm install
npm run build
AGENT_LEDGER_URL=https://ledger.example.com AGENT_LEDGER_API_KEY=... npm start
```

### Hosted ingestion

```bash
cd services/ingestion
npm install
npx wrangler d1 migrations apply agent-ledger --local
npm test
npx wrangler dev
```

See `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/TENANCY_AND_METERING.md`, and `docs/DISTRIBUTION.md`.

## Security / compliance scope

Agent Ledger provides audit-evidence and accountability controls. Deploying it does not itself establish SOC 2, HIPAA, EU AI Act, or other regulatory compliance. Operators remain responsible for access controls, retention, data classification, legal basis, key management, monitoring, incident response, and the rest of their control environment.


## v0.2 commercial control plane

Early-adoption paid pricing is **Starter $20/month, Pro $49/month, Governance $99/month, Scale $249/month**. The Developer tier remains free with 25K events/month. Paid capacities are Starter 50K, Pro 250K, Governance 1M, and Scale 5M events/month, with upgrade prompts beginning at 50% utilization.

Adds lowered entry pricing, tenant billing/entitlements, Venmo QR order and reconciliation flow, masked Venmo billing alias `Venmo_Business_QR`, admin payment verification, and billing API endpoints. The exact Venmo QR image is deployment-configurable through `VENMO_BUSINESS_QR_URL` and is never fabricated from a username.


## v4.4.1 launch control plane
Adds self-service signup/login, RBAC, API-key lifecycle UI, usage console, Stripe-compatible webhooks, retention cron, external signing/anchor hooks, agent/policy inventory, audit search/evidence export, and GitHub release automation. See `docs/DEPLOYMENT.md` and `docs/PUBLISHING.md`.
