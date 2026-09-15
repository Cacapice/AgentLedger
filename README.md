# Agent Ledger

**Evidence infrastructure for statistically validating autonomous AI systems.**

Agent Ledger records consequential agent behavior as structured, tamper-evident evidence for **audit, statistical inference, and operational-boundary validation**. It is designed to answer not only *what did the agent do?*, but also *what evidence supports the behavior, did the observed trajectory remain inside its permitted operating set, and what can we responsibly infer from the observations?*

Agent Ledger complements existing agent frameworks and observability stacks rather than replacing them.

## What distinguishes Agent Ledger

Most audit systems stop at reconstructing actions. Agent Ledger treats recorded transitions as a **measurement substrate** that can be analyzed after execution.

```text
Agent → Action → State transition → Evidence → Outcome
                                      ↓
                           Operational boundary
                                      ↓
                         Statistical validation
```

The architecture separates three concerns and exposes them through a versioned evidence protocol:

1. **Evidence layer (APE 1.0)** — a versioned `AgentProvenanceEvent` Pydantic model and JSON Schema for attribution, state transitions, policy context, provenance, outcomes, and idempotency.
2. **Validation layer** — convert observations into analyzable evidence and summarize boundary violations without turning statistical evidence into a certainty claim.
3. **Operational-boundary layer** — define named predicates representing allowed sets of agent transitions and test observed trajectories against them.


## APE 1.0 — open provenance schema

Agent Ledger now uses **Agent Provenance Event (APE) 1.0** as its canonical evidence representation. The schema is published at `schemas/ape-1.0.schema.json` and is intentionally inference-neutral: producers record evidence; downstream validators decide what that evidence supports.

```python
from agent_ledger import AgentProvenanceEvent

event = AgentProvenanceEvent(
    agent_id="payment_agent",
    agent_version="v2",
    run_id="run_001",
    action="purchase",
    prior_state={"balance": 120},
    resulting_state={"balance": 70},
    provenance={"source": "agent_runtime"},
    idempotency_key="purchase_001",
)
```

APE is an **open schema**, not a claim of industry-standard status. See `docs/APE_STANDARD.md`.

## Safe sets: observe or enforce

Operational boundaries can run passively (`observe`) or prevent invalid transitions (`strict`). A safe set is evaluated over the full observed transition—not merely the action name—so state-dependent constraints remain expressible.

```python
ledger = EvidenceLedger(enforcement="strict")
ledger.define_safe_set(
    "nonnegative_balance",
    lambda e: e.resulting_state["balance"] >= 0,
)
```

In strict mode, an event outside any registered safe set raises `BoundaryViolationError` before it is appended to the validation view. Observe mode records the evidence and allows post-run analysis.

## Posterior Store — Bayesian-ready evidence

The Posterior Store is deliberately a **small export layer**, not a new statistics framework. It turns ledger evidence into analysis-ready observations for notebooks, PyMC, Stan, CSV, or Pandas while keeping inference assumptions outside the ledger.

```python
data = ledger.posterior_dataset(boundary="production_safe_set")

df = data.to_pandas()
pymc_data = data.to_pymc()
stan_data = data.to_stan()
data.to_csv("validation_evidence.csv")
```

This creates a clean division of responsibility:

> **Agent Ledger preserves and structures evidence. PyMC/Stan performs inference.**

## Evidence and boundary validation

The Python SDK now exposes first-class `Evidence`, `OperationalBoundary`, and `EvidenceLedger` primitives.

```python
from agent_ledger import Evidence, EvidenceLedger

ledger = EvidenceLedger()

ledger.define_boundary(
    "production_safe_set",
    lambda e: e.resulting_state["balance"] >= 0,
    description="An agent may not transition to a negative balance.",
)

ledger.record(Evidence(
    agent_id="payment_agent",
    agent_version="v2",
    run_id="run_001",
    action="purchase",
    prior_state={"balance": 120},
    resulting_state={"balance": 70},
    observation={"merchant": "example"},
    outcome="approved",
    provenance={"source": "agent_runtime"},
))

result = ledger.validate("production_safe_set", run_id="run_001")
print(result.to_dict())
```

Validation reports include the number of observed transitions, safe-set membership, violation rate, evidence completeness, and the parameters of a **Beta posterior over the boundary-violation probability**. The posterior is exposed as evidence for downstream analysis—not as a certification claim.

Version-level comparisons are also supported:

```python
results = ledger.compare_versions("production_safe_set")
```

This makes regression analysis a natural extension of the same evidence model.

## Tamper-evident audit trail

The existing audit SDK records consequential actions with:

- agent and actor attribution;
- authority and policy context;
- redacted inputs and output summaries;
- execution status and timing;
- SHA-256 payload and event hashes;
- hash-chain linkage to the previous event;
- optional hosted ingestion receipts.

The CLI verifier can independently check a local JSONL chain for sequence, linkage, and event-hash integrity.

## Design principle

Agent Ledger deliberately separates **observation** from **inference**.

A ledger record establishes what was observed and preserves its provenance. A boundary states the operational set being tested. Statistical analysis describes what the accumulated observations support. Keeping these layers explicit makes validation assumptions inspectable and allows developers to replace or extend the inference method without rewriting the evidence layer.

> Preserve the evidence first. Make the inference explicit. Keep the claim proportional to the evidence.

## v4.4.1 — Self-Service Launch Control Plane

v4.4.1 introduced the self-service commercial control plane for hosted Agent Ledger deployments, including user signup, tenant provisioning, RBAC, API-key lifecycle management, usage controls, agent/policy inventory, audit search, evidence export, retention automation, signing/anchoring hooks, billing entitlements, and deployment automation.

Agent Ledger supports audit and control evidence; deployment does not itself constitute certification or regulatory compliance.

## Commercial tiers — reference

| Tier | Monthly price | Included events / month |
| --- | ---: | ---: |
| Developer | Free | 25,000 |
| Starter | $20 | 50,000 |
| Pro | $49 | 250,000 |
| Governance | $99 | 1,000,000 |
| Scale | $249 | 5,000,000 |
| Enterprise | Custom | Custom |

Usage notifications begin before the monthly event limit is reached. Entitlements and ingestion limits are enforced by the hosted control plane.

## Project boundary

Developer-facing SDKs, schemas, validation primitives, integrations, examples, and MCP tooling are intended for public distribution. The hosted ingestion service, tenant control plane, billing internals, payment reconciliation, credentials, and production infrastructure configuration should remain private.

## Documentation

- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
- `docs/PUBLISHING.md`
- `docs/ACCOUNTABILITY_MODEL.md`
- `docs/EVIDENCE_VALIDATION.md`
- `docs/APE_STANDARD.md`
- `docs/POSTERIOR_STORE.md`

## Scope

Agent Ledger is evidence and validation infrastructure. It does **not** by itself prove that an agent is safe, compliant, correct, or statistically well-calibrated. Those conclusions depend on the operational boundary, evidence quality, sampling process, model assumptions, and validation procedure chosen by the developer.
