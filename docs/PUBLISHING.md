# Public distribution

Recommended public surface: `packages/python`, `packages/typescript`, `apps/mcp`, `schemas`, `examples`, `site`, and public documentation. Keep `services/ingestion` and commercial billing/control-plane internals private unless you intentionally change the licensing model.

## GitHub
Create a public repository for the SDK/distribution surface. Protect `main`, require CI, use signed tags/releases, and enable dependency alerts.

## PyPI
Create the `agent-ledger` project and configure PyPI Trusted Publishing for the GitHub repository/environment named `pypi`. Publishing then occurs when a GitHub Release is published.

## npm
Create/claim the `@agent-ledger` scope, add the repository as a trusted publisher when supported for your account, or temporarily configure `NPM_TOKEN`. The included workflow publishes `@agent-ledger/sdk` with provenance.

## Commercial service
Deploy from a private repository or private subdirectory. Do not publish production secrets, D1 ids, Venmo QR source files that you do not want public, admin tokens, Stripe webhook secrets, or signing credentials.
