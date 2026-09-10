# v4.4.6 — Cloudflare Workers PBKDF2 compatibility fix

Cloudflare Workers WebCrypto rejects PBKDF2 iteration counts above 100,000. v4.4.5 requested 210,000 iterations during signup/login, causing authentication to fail before account creation.

v4.4.6 sets the PBKDF2-SHA256 iteration count to 100,000 and adds regression coverage to prevent the configured count from exceeding the Workers limit.

No D1 migration is required. Redeploy the ingestion Worker. Existing accounts that were successfully created with the same 100,000-round scheme remain compatible; failed signup attempts created no usable account record.
