# Contributing

Changes to runtime/evidence semantics require:
1. a contract/schema change when externally visible;
2. a conformance fixture;
3. tests in the reference Python runtime;
4. parity tests for affected SDKs;
5. migration/compatibility notes when serialized evidence changes.

Run the repository quality gates before opening a PR. Never weaken a test or verification rule solely to make CI green. Security-sensitive changes should include negative/tamper/failure-path tests.
