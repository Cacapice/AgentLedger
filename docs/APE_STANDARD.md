# Agent Provenance Event (APE) 1.0

APE is Agent Ledger's open, versioned JSON schema for exchanging evidence about autonomous-agent transitions. It is an **open schema**, not a claim of industry-standard status.

Canonical schema: `schemas/ape-1.0.schema.json`.

An event identifies the agent/run/action, prior and resulting state, observation/outcome, policy context, confidence, provenance, and optional idempotency key. Consumers should preserve `schema_version`, `event_id`, and `timestamp` when transporting an event.

The schema is deliberately inference-neutral: APE records evidence; validation and statistical models consume it.
