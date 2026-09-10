# @agent-ledger/sdk

Framework-neutral TypeScript client for Agent Ledger.

```ts
import { AuditClient, redact } from "@agent-ledger/sdk";

const client = new AuditClient({baseUrl: "https://ledger.example.com", apiKey: process.env.AGENT_LEDGER_API_KEY!});
await client.record({
  agent_id: "support-agent",
  action_type: "TOOL_CALL",
  tool_name: "crm.update",
  execution_status: "SUCCESS",
  input_parameters: redact({customer_id: "123", api_key: "secret"}).value
});
```
