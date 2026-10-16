# Interoperability and signed provenance

This release adds an OTLP/HTTP JSON **logs exporter**, signed Ed25519 evidence envelopes requiring an out-of-band trusted public key, shared Python/TypeScript RFC 8785 test vectors, and a GitHub Actions build provenance attestation workflow.

## OTLP

`agent_ledger.otlp_export.export_otlp_log(event)` sends a log record to `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` or the `/v1/logs` path under `OTEL_EXPORTER_OTLP_ENDPOINT`. Use a collector and configure TLS/authentication in production. This is a logs exporter only, **not** a complete traces/metrics receiver or OTLP/gRPC implementation. Collector acceptance and retries are not certified.

## Signatures

`make_envelope(payload, private_key, public_key)` and `verify_envelope(envelope, trusted_public_key)` sign RFC8785 canonicalized bytes with Ed25519. Distribute the trusted public key through an authenticated channel; embedded keys alone are not trustworthy. Key rotation, revocation, HSM integration and external timestamping remain operational requirements.

## Provenance

Tag pushes or manual dispatch run `.github/workflows/signed-provenance.yml` and request GitHub's Sigstore-backed signed build provenance. Verification (after the GitHub run succeeds): `gh attestation verify PATH_TO_WHEEL --repo OWNER/REPO`. The workflow requires GitHub Actions attestation permissions. Signing cannot be executed locally without a GitHub-issued identity; no attestation is bundled with source.

## Test

`pip install -e 'packages/python[crypto,test]' && pytest packages/python/tests/test_interop_2026.py`

`cd packages/typescript && npm ci && npm test`

Do not claim full RFC8785 conformance from the small fixture set alone. Full official vectors, multiple language versions, fuzzing, and live collector integration are release gates.
