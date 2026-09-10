# Agent Ledger

**A tamper-evident accountability layer for autonomous AI agents.**

Agent Ledger records consequential agent actions with attribution, authority, policy context, results, and verifiable audit evidence. It is designed to support operational governance and audit evidence without replacing the developer's existing agent framework or observability stack.

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

