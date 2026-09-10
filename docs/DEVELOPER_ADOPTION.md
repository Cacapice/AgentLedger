# Developer adoption
## Five-minute path
1. `pip install agent-ledger` or `npm install @agent-ledger/sdk`.
2. `agent-ledger init` and set the hosted URL/key.
3. Wrap one consequential action or add the OpenAI trace processor.
4. Execute the action and capture the returned `receipt_id`.
5. `agent-ledger verify alr_...`.

## Distribution
Ship public Python/TypeScript SDKs, CLI, MCP server, schemas, verifier, integrations and runnable examples. Keep hosted billing, tenant control-plane internals and production credentials private.

Prioritize developers whose agents can send email, mutate databases, merge code, issue refunds, purchase items or deploy software. The free tier must include receipts and verification; paid tiers monetize scale and organizational control.
