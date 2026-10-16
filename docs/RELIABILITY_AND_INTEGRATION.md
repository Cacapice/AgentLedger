# Reliability and integration qualification

AgentLedger provides agent evidence infrastructure, not an external certification. APE is project-defined; OTLP and RFC 8785 are interoperability targets.

## Release gates

1. Run `python -m pip install -e "packages/python[crypto,test,production]"` then `python -m ruff check --select F packages/python/src packages/python/tests`, `python -m mypy packages/python/src/agent_ledger`, and `python -m pytest packages/python/tests -q`.
2. Run `npm ci`, `npm run build`, and `npm test` at repository root. Require Go/Rust tests and integration workflows to pass.
3. Run the reliability smoke test (`python -m pytest packages/python/tests/test_reliability_smoke.py -q`). It demonstrates rejection of modified evidence and revoked/rotated signing keys; it is not a replacement for production KMS and timestamped revocation records.
4. Run live collector integration against a pinned OpenTelemetry Collector release, verify all three OTLP signals and retry/partial-success behavior. Workflow presence alone is not proof of interoperability.
5. Verify canonical JSON fixtures against independent RFC 8785 implementations in Python and TypeScript; verify supported IEEE-754 edge cases and reject non-finite numbers.
6. On a version tag, require a successful build, attest artifacts using GitHub artifact attestations, download the exact artifact, and verify it with `gh attestation verify <artifact> --repo Cacapice/AgentLedger`. A workflow definition is not an issued attestation.
7. Record the release commit SHA, artifact SHA-256, test results, supported platform matrix, and known limitations.

## Independent review

Invite reviewers to test threat models: key compromise and revocation timing; hash-chain tampering; tenant boundary bypass; replay/idempotency under concurrency; exporter downtime and partial acceptance; and provenance identity spoofing. Capture issues and remediation links.

## Adoption evidence

Publish a minimal integration walkthrough with one genuine agent invocation, evidence export, independent signature verification, a tampering failure, and a recovery demonstration. Measure setup time and report external user feedback without implying adoption where none is documented.

## Shared evidence contract

APE is the AgentLedger-native schema. For other research repositories, provide an optional adapter mapping: `source_id`, `experiment_or_run_id`, `claim`, `method_version`, `artifact_digest`, `observation`, `limitations`, and `provenance`. This is a proposed integration contract, not a ratified standard.
