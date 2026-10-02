# High-impact differentiation roadmap

The project should compete on **verifiable operational truth**, not number of integrations.

## 1. Portable Evidence Bundle (highest impact)
Export a run as a self-verifying package: RFC 8785 canonical records, ordered Merkle commitments, Ed25519 manifest, public-key material, policy/config hashes, causal IDs, optional encrypted blobs, and an offline verifier. This turns audit data into portable evidence across vendors and organizations.

## 2. Effect Reconciliation Registry
Standardize reconcilers for payments, tickets, email, files and API writes. `UNKNOWN` is useful only if operators can cheaply determine whether the side effect happened. Provider-specific reconcilers can make crash recovery materially safer than generic retry engines.

## 3. Causal + OpenTelemetry bridge
Carry `trace_id`, `span_id`, workflow ID, run/step/effect IDs and causal parent through MCP/framework boundaries. Export runtime evidence to OTLP while keeping signed evidence authoritative. This gives teams normal observability without turning traces into the source of truth.

## 4. Evidence-aware policy simulation
Run a proposed policy against historical signed evidence without replaying side effects: "which past actions would this policy deny/approve/escalate?" This makes policy rollout measurable and lowers governance adoption risk.

## 5. SLO / reliability scorecards from evidence
Compute duplicate-effect rate, UNKNOWN reconciliation latency, lease-loss rate, replay divergence, policy-denial rate, cost per successful run and version regressions. Every metric should link back to evidence rather than opaque telemetry.

## 6. Cross-organization verification
Allow a recipient of an agent action to verify a minimal receipt without access to the sender's entire ledger. Selective disclosure / inclusion proofs are a natural extension of the existing Merkle run manifests.
