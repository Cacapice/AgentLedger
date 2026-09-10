# OpenAI Agents integration
Agent Ledger can be installed as an additional tracing processor so existing OpenAI Agents traces remain available while consequential spans are copied to the ledger.

```python
from agents import add_trace_processor
from agent_ledger import AgentLedgerProcessor
add_trace_processor(AgentLedgerProcessor())
```
Set `AGENT_LEDGER_URL` and `AGENT_LEDGER_API_KEY`. Review sensitive-data settings before exporting traces.
