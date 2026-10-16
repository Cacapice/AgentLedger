# Release checklist (complete for every tag)

- [ ] CI: Python, TypeScript, MCP, Go, Rust checks green
- [ ] Reproducible dependency installation documented; lockfiles reviewed
- [ ] Collector integration and failure-injection jobs green
- [ ] Independent evidence verification and key revocation tests green
- [ ] RFC 8785 Python/TypeScript parity green
- [ ] Security review and dependency scanning green
- [ ] SBOM and SHA-256 manifests published
- [ ] GitHub attestation created for exact release artifact
- [ ] Downloaded artifact independently verified against expected repository
- [ ] Changelog, compatibility matrix, limitations and rollback documented
- [ ] At least one external reviewer or user validation recorded (or explicitly pending)

Do not mark a release production-certified solely because this checklist exists.
