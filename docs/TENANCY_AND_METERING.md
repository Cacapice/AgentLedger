# Tenancy and metering

Tenant isolation is enforced at the database query layer: every key resolves to exactly one `tenant_id`, and every event, chain head, idempotency key, and usage row is keyed by that tenant.

Plans supported by the schema: `developer`, `pro`, `governance`, `scale`, `enterprise`.

Metered dimensions in v0.1:

- accepted events;
- accepted serialized bytes;
- failed execution events;
- policy-blocked events.

Hourly counters provide a billing/export primitive without coupling the product to one payments provider. `monthly_event_limit` can be null for contract/unlimited tenants or an integer for self-service plans.

Recommended commercial mapping:

- Developer: free, low event cap, short retention.
- Pro: higher cap + API access.
- Governance: policy/HITL/evidence features.
- Scale: SSO, long retention, exports.
- Enterprise: negotiated usage, BYOC/data residency/SLA.

Billing should derive invoices from immutable usage exports or a separate billing ledger rather than relying only on mutable dashboard totals.


## Early-adoption commercial thresholds (v0.2)

| Plan | Monthly price | Events / month | Retention |
|---|---:|---:|---:|
| Developer | $0 | 25,000 | 30 days |
| Starter | $20 | 50,000 | 30 days |
| Pro | $49 | 250,000 | 30 days |
| Governance | $99 | 1,000,000 | 30 days |
| Scale | $249 | 5,000,000 | 30 days |
| Enterprise | Contract | Custom | Up to 7 years default |

These deliberately low thresholds are intended for market entry and can be revised through the plan catalog without changing SDK contracts.

## Venmo QR checkout

Public checkout surfaces use the neutral alias `Venmo_Business_QR`. The underlying destination username is held only in private Worker configuration through `VENMO_BUSINESS_USERNAME`.
The bundled checkout uses `site/assets/Venmo_Business_QR.jpg` by default. `VENMO_BUSINESS_QR_URL` is an optional deployment override. The site/API never treats a QR scan as proof of payment.

Flow: create order -> display exact amount + QR + unique payment note -> buyer pays -> buyer submits Venmo transaction reference -> payment remains `submitted` -> admin/provider verification -> entitlement activates.

For fully automatic settlement, configure a PayPal Business/Developer integration and Venmo checkout/webhooks. Static QR checkout intentionally fails closed until settlement is verified.

## Upgrade pressure policy

Paid plans now use earlier capacity signals: at **50%** usage the API returns a notice, at **75%** an upgrade recommendation, at **90%** an urgent warning, and at **100%** new ingestion is blocked until the tenant upgrades or the monthly period resets. The Developer tier remains 25K events/month; paid-tier capacities are intentionally tighter to accelerate conversion while preserving a usable evaluation path.

## Monthly Venmo auto-renew default
Paid subscriptions default to `billing_interval=monthly` and `auto_renew=true`, with Venmo as the preferred payment method. Automatic recurring charging is only attempted after a customer has completed a recurring-payment authorization through a configured Venmo-capable provider adapter. The static `Venmo_Business_QR` remains a fallback and is never treated as recurring debit authorization.

Configure `VENMO_RECURRING_SETUP_URL`, `VENMO_RECURRING_CHARGE_URL`, and `VENMO_RECURRING_TOKEN` to connect a provider adapter. Without those values, subscription creation remains monthly/auto-renew by policy but returns an action-required QR order for the current period rather than attempting an unsupported debit.
