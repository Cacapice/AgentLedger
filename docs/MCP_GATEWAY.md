# MCP accountability gateway
The packaged MCP server exposes `audit_record`, `audit_get_receipt`, `audit_check_policy`, `audit_usage`, and `audit_verify_file`. It can be placed beside an MCP tool server so the host evaluates policy and records a receipt before/after consequential calls.

A transparent HTTP reverse proxy is **not** claimed in this release: MCP 2026-07-28 uses stateless requests and header-based routing, but production gateway authorization requires OAuth/resource-server integration and explicit user consent. The included server is the safe instrumentation/control primitive for that next step.
