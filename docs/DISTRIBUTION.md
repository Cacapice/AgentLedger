# Distribution and commercialization

## Open distribution

Publish `packages/python` to PyPI as `agent-ledger`, `packages/typescript` to npm as `@agent-ledger/sdk`, and `apps/mcp` to npm as `@agent-ledger/mcp`. Mirror source to a public GitHub repository and attach signed release checksums.

## Commercial distribution

Keep `services/ingestion` in a private repository or a separately permissioned monorepo path before public release. Offer the service as hosted SaaS and, for enterprise contracts, as an authorized BYOC/self-hosted deployment.

## License boundary

Apache-2.0: SDKs, CLI, MCP server, examples, developer site.

Commercial: hosted ingestion, tenant control plane, billing/metering backend extensions, enterprise policy/evidence services.

The provided commercial notice is a placeholder product boundary and should be replaced by counsel-approved licensing and customer terms before accepting payment.

## Release checklist

1. Reserve package names and product/domain marks.
2. Replace placeholder commercial license and privacy/terms text with counsel-approved versions.
3. Configure CI for Python/Node tests, dependency scanning, SBOM, artifact signing, and release provenance.
4. Provision production D1, secrets, rate limiting, alerting, retention jobs, backups, and external integrity anchors.
5. Create tenant/admin provisioning that emits one-time API keys; never store raw keys.
6. Add payments only after metering reconciliation and entitlement tests pass.
