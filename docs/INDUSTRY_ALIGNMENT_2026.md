# AgentLedger industry alignment — October 2026

This document distinguishes **implemented controls**, **integration targets**, and **unverified claims**. No certification is implied.

## Engineering baseline

- **Evidence**: preserve schema-versioned events, stable identifiers, actor/agent attribution, timestamps, explicit execution status, and integrity-verification results. APE 1.0 is project-defined, not an externally ratified standard.
- **Interoperability**: map run and tool spans to OpenTelemetry and W3C Trace Context; propagate trace IDs across asynchronous execution and tool boundaries. Validate mappings with cross-process integration tests.
- **API contracts**: publish versioned OpenAPI schemas for hosted endpoints; define authentication, idempotency, pagination, error semantics, and backward-compatibility policy.
- **Security**: use least-privilege credentials, tenant-isolation tests, input validation, secret redaction, dependency scanning, and incident disclosure procedures. Do not place sensitive raw tool inputs in immutable audit events by default.
- **Integrity**: document canonicalization rules (RFC 8785 where applicable), key identifiers, signing algorithms, signature verification, rotation/revocation, chain anchors, and the distinction between tamper-evidence and proof of correctness.
- **Supply chain**: publish SBOMs, immutable release artifacts, provenance attestations, pinned GitHub Actions by commit SHA, and reproducible lockfile installs. Release gates must verify published artifacts, not merely source builds.
- **Quality**: test supported Python/Node versions, SDK parity, MCP protocol compatibility, storage failure/retry behavior, distributed concurrency, and restoration from backups.
- **Operations**: define service-level indicators for ingestion success, evidence lag, verification failures, and export latency; instrument alerts and document retention/deletion policy by tenant.
- **Governance**: document how features support evidence collection relevant to SOC 2, EU AI Act logging, and regulated workflows, without asserting that the product itself guarantees compliance.

## Applied in this update

- Replaced deprecated Python license table with SPDX expression and removed obsolete classifier.
- Installed Python optional production dependencies and type stubs in CI type-check environment.
- Unified TypeScript compiler major/minor ranges across SDK and MCP.
- Added an MCP compilation gate.

## Outstanding before a production-ready claim

1. Run the complete CI matrix with real registry/network access and repair any failing tests.
2. Add committed npm lockfiles and change CI from `npm install` to `npm ci` once lockfiles are generated.
3. Pin CI actions to reviewed commit hashes; check action major versions against actual published tags.
4. Add threat modeling, tenant-boundary penetration tests, and documented recovery drills.
5. Produce signed SBOMs, release provenance, and external evidence-anchor verification.
6. Verify end-to-end OpenTelemetry propagation and independent cryptographic verification across SDK languages.
7. Publish a support matrix, compatibility policy, and benchmark methodology with measured results.

**Status:** alignment improvements applied; certification, compatibility, and production readiness are **not yet verified**.
