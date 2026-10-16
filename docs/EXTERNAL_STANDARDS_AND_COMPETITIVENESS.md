# External standards alignment and competitive positioning (October 2026)

## Important scope statement
APE 1.0 remains a **vendor-defined extension**, not an externally ratified standard. AgentLedger interoperates with external standards through explicitly tested mappings. Neither interoperability nor a control crosswalk means ISO certification, SOC 2 attestation, EU AI Act compliance, or official endorsement.

## Normative and established references

| Reference | AgentLedger treatment | Verification gate |
|---|---|---|
| W3C Trace Context | Validate `traceparent` version 00; existing OTEL inject/extract integration | malformed/all-zero trace identifiers rejected; cross-process propagation tests needed |
| OpenTelemetry traces and logs | Export evidence identifiers and agent metadata without raw prompt/output by default | collector-backed integration and cardinality/privacy tests needed |
| OpenTelemetry GenAI semantic conventions | Map agent/tool spans where stable; track **Development** fields separately | versioned compatibility matrix and integration tests needed |
| RFC 8785 JSON Canonicalization Scheme | Existing JCS module; do not assert full conformance without official vectors and cross-language parity | RFC vectors, UTF-16 ordering, float edge cases and negative tests |
| RFC 9162 transparency architecture | Merkle inclusion/consistency proof model as a design target, not a claimed conformance | independent verifier, consistency and tamper tests |
| RFC 7515 / RFC 8037 signatures | Standard JWS / OKP envelopes as interoperability target; avoid home-grown signing formats for public exchanges | test vectors, rotation and key revocation tests |
| OpenAPI 3.1 / JSON Schema | Publish machine-readable public HTTP contract; APE remains an extension | schema lint, contract tests, generated client smoke tests |
| SPDX / CycloneDX / SLSA | Generate SBOMs and signed provenance for releases | CI release artifacts, provenance verification, dependency scanning |
| OWASP AISVS 1.0 | Security verification checklist for AI and agent systems | versioned control-to-test evidence matrix; no blanket compliance claim |
| ISO/IEC 42001:2023 / NIST AI RMF | Customer evidence export and governance control mapping | audited controls and organization-specific gap assessment |

## Competitive product bar

1. **Evidence, not dashboards alone**: independently verifiable run manifests, signatures, proof verification, immutable audit event links, selective disclosure.
2. **Observability interoperability**: OTel-native propagation, trace/span links, exporter integration and consistent correlation across Python, TypeScript, Go, Rust and MCP.
3. **Policy and effect integrity**: before/after policy decisions, provider effect reconciliation, replay and divergence reports; explicitly report unobservable external effects.
4. **Enterprise controls**: tenant isolation, least-privilege scoped credentials, retention and legal hold, KMS rotation, deletion semantics, audit export and SSO/SCIM roadmap.
5. **Developer experience**: published SDKs, maintained framework adapters, stable OpenAPI, five-minute onboarding, compatibility matrix and conformance suites.
6. **Operational readiness**: multi-region disaster recovery, SLOs, signed release provenance, vulnerability response SLAs, documented incident response and real integration tests.

## Delivered in this revision

- `standards_bridge.py`: strict W3C traceparent version-00 parser and privacy-preserving OTel attribute mapping.
- Focused unit tests for trace ID validation and content redaction.
- Standards-versus-product-specific classification and transparent release gates.

## Outstanding (do not market as complete)

- Official RFC 8785 cross-runtime conformance suite; OTLP collector interoperability; signed provenance and reproducible release pipeline.
- JWS / RFC 9162 interoperability and independent verification; OpenAPI 3.1 contracts and generated clients.
- External security review, pentest, SOC 2 attestation or ISO certification, enterprise tenancy penetration tests.

### Primary specifications

- https://www.w3.org/TR/trace-context/
- https://opentelemetry.io/docs/specs/semconv/
- https://www.rfc-editor.org/rfc/rfc8785
- https://www.rfc-editor.org/rfc/rfc9162
- https://owasp.github.io/www-project-artificial-intelligence-security-verification-standard-aisvs-docs/
- https://www.iso.org/standard/42001
- https://www.nist.gov/itl/ai-risk-management-framework
