"""Small bridge for recording OpenTelemetry-like span dictionaries as Agent Ledger evidence."""
from .core import AuditLogger
class OTelBridge:
    def __init__(self, logger=None): self.logger=logger or AuditLogger.from_env()
    def record_span(self, span):
        attrs=span.get("attributes",{})
        return self.logger.log_event(agent_id=str(attrs.get("gen_ai.agent.name",attrs.get("service.name","otel-agent"))),tool_name=str(attrs.get("gen_ai.tool.name",span.get("name","span"))),action_type="OTEL_SPAN",input_params=attrs,output={"status":span.get("status")},trace_id=span.get("trace_id"))
