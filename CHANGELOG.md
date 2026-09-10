## 0.4.1 — 2026-09-10
- Fixed deployment packaging so nested `npm install` does not query the public registry for unpublished `@agent-ledger/sdk`.
- MCP now resolves the bundled TypeScript SDK through `file:../../packages/typescript`.
- Aligned monorepo package versions to 0.4.1.

## 0.4.0 — 2026-09-10
- Agent Operations: fleet health, loop detection, version regression, failure clustering, and `doctor --production`.

## 0.3.2 — 2026-09-10

- Added canonical Scuderia dogfood command `agent-ledger dogfood-scuderia`.
- The demo performs a real read-only live indexability observation of the Scuderia Maxima page and records it as `scuderia-indexability-agent`.
- Python SDK now exposes the hosted ingestion acknowledgement/`alr_...` receipt on the returned in-memory event without changing the persisted local hash-chain record.
- Added canonical five-minute quickstart and public-demo documentation.
- New signup first SDK keys include `audit:read` so newly created developers can record and immediately verify their first receipt. Existing keys are unchanged and may need an `audit:read` replacement key.
- Added regression coverage proving hosted receipt metadata does not invalidate the local source chain.

## 0.3.1 — 2026-09-10

- Fixed monorepo workspace dependency alignment so `npm install` from `services/ingestion` resolves the bundled `@agent-ledger/sdk` workspace instead of querying npm for unpublished `@agent-ledger/sdk@0.2.0`.
- Aligned MCP and TypeScript SDK package versions at 0.3.1.

## 0.3.0 — 2026-09-10
- Developer Adoption Release: action receipts, verify API/CLI, OpenAI Agents processor, OTel bridge, policy primitive, MCP receipt/policy tools, six examples.

## 0.2.2 — 2026-09-10

- Paid billing defaults to monthly auto-renew with Venmo preferred.
- Added recurring Venmo provider-adapter hooks and scheduled renewal processing.
- Added safe `Venmo_Business_QR` fallback when recurring authorization is unavailable.
- Added subscription status/cancellation endpoints and migration `0006_monthly_venmo_autorenew.sql`.
- QR payment is explicitly not treated as recurring-debit authorization.

## v4.4.3 — Masked Venmo Business QR

- Embedded the provided Venmo business QR as `site/assets/Venmo_Business_QR.jpg`.
- Public checkout/API surfaces use the neutral alias `Venmo_Business_QR`; the underlying Venmo destination remains private server configuration.
- External `VENMO_BUSINESS_QR_URL` remains an optional override.
- Removed the public Venmo profile link/username from checkout payloads and UI.
- Corrected the Scale plan retention constant to 30 days and added regression coverage enforcing 30-day retention across every tier.

## v4.4.2 — Uniform 30-Day Retention
- Standardized tenant audit-event retention to 30 days across Developer, Starter, Pro, Governance, Scale, and Enterprise.
- Added forward migration 0005 to update existing tenants and plan catalog entries.
- Updated signup defaults, provisioning defaults, billing entitlements, retention fallback, pricing site, and tenancy documentation.

## v4.4.1 — Self-Service Launch
- Completed signup/login/tenant provisioning, RBAC, API-key management, dashboard, Stripe-compatible entitlements, retention, external anchor/signing hooks, inventory, audit search/export and package release automation.

## v0.3.0 / Scuderia v4.4.0

- Added commercial SaaS billing/control-plane routes with Venmo checkout defaults for `Venmo_Business_QR`.
- Added tenant-scoped Venmo order creation, payment-reference submission, admin verification/rejection, and verified-payment entitlement activation.
- Set self-service pricing to Starter $20, Pro $49, Governance $99, Scale $249 per month.
- Tightened paid event capacity to 50K / 250K / 1M / 5M events per month.
- Added upgrade-pressure signals at 50%, 75%, and 90% utilization, with hard ingestion stop at 100%.
- Added forward migration `0003_tighten_paid_capacity.sql` for existing tenants.

# Changelog

## 0.1.0 — 2026-09-10

Initial distributable product extraction from the Scuderia v4.3.8 audit subsystem.

Added Python SDK/CLI, TypeScript SDK, MCP server, commercial hosted-ingestion Worker, D1 multi-tenant schema, hourly usage metering, API-key hashing/scopes, idempotent event ingestion, OpenAPI contract, product licensing boundary, examples, architecture/distribution documentation, and developer landing page.

## 0.2.0 — 2026-09-10

Commercial SaaS control-plane foundation: tenant billing and entitlement periods, Venmo QR/manual reconciliation flow, admin verify/reject actions, checkout UI, and lower early-adoption thresholds. Current monthly pricing: Developer $0, Starter $20, Pro $49, Governance $99, Scale $249. Public Venmo billing alias: `Venmo_Business_QR`; exact QR image remains deployment-configurable via `VENMO_BUSINESS_QR_URL`.
