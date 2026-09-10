# OpenTelemetry bridge
`agent_ledger.OTelBridge` accepts normalized span dictionaries and maps common `service.name`, `gen_ai.agent.name`, and `gen_ai.tool.name` attributes into Agent Ledger actions. This is intentionally an adapter boundary rather than a competing telemetry format.
