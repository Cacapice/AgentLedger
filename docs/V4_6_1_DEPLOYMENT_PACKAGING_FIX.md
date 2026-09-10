# v4.6.1 — Deployment Packaging Fix

This release fixes `npm install` from `services/ingestion` attempting to fetch unpublished `@agent-ledger/sdk` from npm.

`apps/mcp/package.json` now references the bundled SDK explicitly:

```json
"@agent-ledger/sdk": "file:../../packages/typescript"
```

This preserves the open-core monorepo while making the deployment archive self-contained with respect to the internal SDK. External dependencies such as Wrangler, the MCP SDK, Zod, and TypeScript are still installed from npm.
