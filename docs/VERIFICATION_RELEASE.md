# Verification release — October 2026

## OTLP
Python OTLP/HTTP JSON supports logs, traces, metrics, per-signal endpoints, bounded exponential jitter, and partial rejection detection. The collector smoke workflow uses an actual OpenTelemetry Collector. gRPC and HTTP/protobuf are **not** implemented by this custom transport; use upstream OpenTelemetry SDK exporters for those protocols. CI must run in GitHub before collector integration can be claimed green.

## Keys
`KeyRegistry` supports explicit public-key trust, rotation, and revocation. Trust registry persistence, authenticated distribution, trusted timestamps, and historical validation policies remain deployment responsibilities. Do not trust keys merely because they are embedded in signed evidence.

## Provenance
`.github/workflows/signed-provenance.yml` creates GitHub attestations when triggered in the upstream repository. A local ZIP cannot produce a GitHub-signed attestation. After workflow success, retrieve the built artifact and run:

```bash
gh attestation verify ./agent_ledger-*.whl --repo OWNER/REPO
```

The verifying user must independently establish the trusted repository identity and expected workflow/ref. Keep build and attestation in the same workflow run. Review GitHub Actions run permissions and attestation availability for your plan.

## Canonicalization
The shared Python/TypeScript vectors are a regression baseline, **not** the full RFC 8785 conformance suite. Full coverage requires upstream reference vectors including IEEE-754 edge cases and surrogate handling. Run both language suites on the same corpus before asserting RFC 8785 conformance.
