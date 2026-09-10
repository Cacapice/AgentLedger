# Launch readiness — v4.4.1

Implemented in this release:
- self-service signup/login and automatic Developer tenant provisioning
- tenant owner membership and session authentication
- RBAC-enforced control-plane routes
- API-key list/create/rotate/revoke UI and API
- usage dashboard with upgrade-pressure meter
- provider-neutral entitlements plus Stripe-signature webhook processing
- Venmo Venmo_Business_QR manual verified-payment path
- hourly per-plan retention enforcement
- chain-head signing hook and independent external anchoring hook
- normalized agent and policy inventory
- audit search and evidence JSON export
- GitHub CI, GitHub Releases, PyPI Trusted Publishing workflow and npm Trusted Publishing workflow

Production dependencies that remain operator configuration rather than code gaps:
- actual domain/DNS
- actual D1 database id
- your hosted Venmo QR URL
- Stripe webhook secret and checkout price/session creation if Stripe is enabled
- external KMS/signing endpoint and/or independent anchoring endpoint
- PyPI/npm/GitHub project ownership and trusted-publisher registration
- final commercial legal terms and privacy/retention policy review
