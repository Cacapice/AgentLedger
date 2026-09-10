# agent-ledger (Python)

Open-source Python instrumentation, hosted-ingestion client, and offline verifier for Agent Ledger.

```bash
pip install agent-ledger
agent-ledger verify audit_events.jsonl
```

Environment variables:

- `AGENT_LEDGER_URL` — hosted ingestion base URL.
- `AGENT_LEDGER_API_KEY` — tenant API key.
- `AGENT_LEDGER_LOG` — local JSONL path (default `./audit_events.jsonl`).
- `AGENT_LEDGER_CHAIN_ID` — optional local chain identifier.
