# Security Policy

## Supported versions
Security fixes are applied to the latest minor release.

## Reporting
Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting for this repository when enabled, or contact the repository owner privately.

Include affected version, reproduction, impact, and whether credentials or external side effects are involved. Do not include live secrets.

## Security boundaries
AgentLedger evidence is tamper-evident, not a substitute for authorization, sandboxing, secret management, or provider controls. `UNKNOWN` effects must be reconciled against provider truth and must not be blindly retried.
