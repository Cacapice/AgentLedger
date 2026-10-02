# Framework-native end-to-end examples

These examples keep the framework in charge of planning and place AgentLedger at the side-effect boundary. They are intentionally small and require the named framework as an optional dependency.

* `langgraph_native.py` — LangGraph node/tool boundary
* `openai_agents_native.py` — OpenAI Agents SDK function-tool boundary
* `crewai_native.py` — CrewAI tool boundary pattern

All use the same `RuntimeAdapter.wrap_tool` semantics, so a lost acknowledgement becomes `UNKNOWN` rather than an unsafe automatic retry.
