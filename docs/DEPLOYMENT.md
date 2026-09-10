# Production deployment

Deploy the commercial ingestion/control plane separately from the public SDK repository surface.

## Required Cloudflare resources
- Worker: `agent-ledger-ingestion`
- D1 database: `agent-ledger`
- Cron: hourly at minute 17 for retention + chain anchoring

## Secrets
Use `wrangler secret put` for: `ADMIN_TOKEN`, `STRIPE_WEBHOOK_SECRET`, `ANCHOR_SIGNING_TOKEN`, `ANCHOR_WEBHOOK_TOKEN`, `ANCHOR_HMAC_SECRET` (fallback only). Do not commit these values.

## Configuration
Set `VENMO_BUSINESS_USERNAME=ArcanaImperi`. Set `VENMO_BUSINESS_QR_URL` to the hosted business QR image. For external signing use `ANCHOR_SIGNING_URL`; the signing endpoint must return `{signature,key_id,provider}`. For independent anchoring set `ANCHOR_WEBHOOK_URL`.

## Deploy
1. `cd services/ingestion`
2. `npm install`
3. `npx wrangler d1 create agent-ledger` (first deployment only)
4. Put the returned database id into `wrangler.jsonc`.
5. `npx wrangler d1 migrations apply agent-ledger --remote`
6. Add secrets with `npx wrangler secret put ...`.
7. `npm test`
8. `npx wrangler deploy`
9. Deploy `site/` to Cloudflare Pages or another static host and point its API base URL at the Worker.
10. Create a real signup through `site/app.html`; use the returned first API key for SDK testing.

## Smoke test
- `GET /healthz`
- create account through `/v1/auth/signup`
- `GET /v1/auth/me`
- ingest one SDK event with the one-time `al_` API key
- verify the event appears in audit search and usage
- create/rotate/revoke a second key
- verify Venmo order creation and payment reconciliation in test operations
- if Stripe is enabled, send a signed test webhook
- confirm cron creates a chain anchor and records a retention run

## Masked Venmo QR asset

The bundled checkout serves `site/assets/Venmo_Business_QR.jpg` by default. Public UI/API responses identify it only as `Venmo_Business_QR`. Keep `VENMO_BUSINESS_USERNAME` in private Worker configuration for operator reconciliation. Set `VENMO_BUSINESS_QR_URL` only when you intentionally want to override the bundled asset with a hosted QR.

### Automatic monthly Venmo billing
Automatic monthly renewal is the paid-plan default. To enable actual recurring Venmo charges, connect a recurring-payment adapter and set these Worker secrets/variables:

- `VENMO_RECURRING_SETUP_URL` — creates the customer authorization agreement and returns an approval URL/provider subscription reference.
- `VENMO_RECURRING_CHARGE_URL` — requests an authorized monthly renewal charge.
- `VENMO_RECURRING_TOKEN` — bearer token for those adapter calls (store as a Worker secret).

If the adapter is not configured, Agent Ledger safely falls back to the embedded `Venmo_Business_QR` and creates an action-required renewal order. Never treat a QR scan as authorization for a recurring debit.


## Browser console / CORS
The static site and Worker normally run on different origins. Configure `ALLOWED_ORIGINS` in `services/ingestion/wrangler.jsonc` to the comma-separated Pages/custom origins that may call the API. The packaged default is `*` for initial bring-up; replace it before production launch, for example `https://app.agentledger.example,https://agent-ledger.pages.dev`. Redeploy the Worker after changing it. The Worker handles browser OPTIONS preflight for Authorization and JSON requests.
