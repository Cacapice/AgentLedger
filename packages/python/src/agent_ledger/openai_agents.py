"""Optional OpenAI Agents SDK trace processor. No OpenAI dependency is required until used."""
from .core import AuditLogger
class AgentLedgerProcessor:
    def __init__(self, logger=None): self.logger=logger or AuditLogger.from_env()
    def on_trace_start(self, trace): pass
    def on_trace_end(self, trace): pass
    def on_span_start(self, span): pass
    def on_span_end(self, span):
        data=getattr(span,"span_data",None) or getattr(span,"data",None)
        name=getattr(data,"name",None) or data.__class__.__name__ if data else "span"
        self.logger.log_event(agent_id="openai-agents",tool_name=str(name),action_type="TRACE_SPAN",input_params={"span_id":getattr(span,"span_id",None)},output={"trace_id":getattr(span,"trace_id",None)},trace_id=getattr(span,"trace_id",None))
    def shutdown(self): pass
    def force_flush(self): pass
