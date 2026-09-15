# Evidence Validation

Agent Ledger models agent behavior as observations that can be preserved independently from the claims later made about them.

## Objects

- `Evidence`: an observed agent action/state transition with outcome and provenance.
- `OperationalBoundary`: a named predicate defining membership in an allowed set of transitions.
- `ValidationResult`: descriptive boundary counts, evidence completeness, and Beta posterior parameters for the violation probability.
- `EvidenceLedger`: a lightweight analysis view for recording evidence, validating runs, and comparing versions.

## Statistical interpretation

For `v` observed violations among `n` transitions and a `Beta(alpha, beta)` prior, validation returns:

`Beta(alpha + v, beta + n - v)`.

This is a posterior over a Bernoulli boundary-violation probability under that model. It is not a safety certification. Dependence between transitions, selection effects, incomplete evidence, boundary misspecification, and distribution shift can all invalidate naive interpretations.

## Boundary example

```python
ledger.define_boundary(
    "tool_allowlist",
    lambda e: e.action in {"search", "retrieve", "summarize"},
)
```

A boundary is intentionally application-defined. Agent Ledger preserves the rule name and evidence so that the validation assumption remains visible and auditable.
