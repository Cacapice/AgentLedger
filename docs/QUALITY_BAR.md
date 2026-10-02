# Quality bar

AgentLedger does not self-award a quality score from feature count. A 9.5/10 release target means
the following domains have objective gates and no known critical/high-severity defect:

| Domain | Required evidence |
|---|---|
| Architecture | versioned contracts, compatibility policy, bounded modules |
| Correctness | unit + invariant + negative-path tests |
| Cryptography | RFC8785 vectors, signature/tamper tests, Merkle inclusion tests |
| Reliability | durable state, fencing, UNKNOWN reconciliation, failure injection |
| Storage | real PostgreSQL/MySQL/MinIO certification |
| Interoperability | Python/TS/Go/Rust conformance fixtures |
| Security | least privilege workflows, dependency audit, CodeQL, SECURITY.md |
| Developer experience | quickstart, examples, buildable packages, stable errors |
| Observability/evidence | OTEL propagation plus independently verifiable evidence |
| Operations | leases, budgets, cancellation, SLO scorecards |
| Documentation | architecture/API/compatibility/security/release docs |
| Release/supply chain | synchronized versions, reproducible package build, tagged release gates |

A release is not represented as meeting the target until required GitHub CI jobs pass. Environment-
dependent integration checks are not converted into mocked passes.
