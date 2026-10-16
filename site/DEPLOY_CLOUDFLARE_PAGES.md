# Cloudflare Pages deployment

This directory is the static Pages output (`site/`). Deploy it to the existing Cloudflare Pages project named `agentauth`:

```bash
npx wrangler login
npx wrangler pages deploy site --project-name agentauth --branch main
```

Run from the repository root. Confirm the production URL in the Cloudflare Pages dashboard. The supplied `f434b577.agentauth.pages.dev` address appears to be a deployment-specific URL, so a new deployment may have a different hash. Check the project's canonical `agentauth.pages.dev` domain and custom domains.

Before deployment, confirm that links to `app.html` and `../openapi.yaml` resolve in the actual Pages output; those assets are not included in this static site directory. Do not claim an attestation or full RFC 8785 conformance until CI passes.
