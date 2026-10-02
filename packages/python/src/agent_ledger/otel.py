"""Optional OpenTelemetry/W3C propagation bridge."""
from __future__ import annotations
from dataclasses import replace
from typing import MutableMapping
from .causal import CausalContext

def _otel():
    try:
        from opentelemetry import trace, propagate
        return trace, propagate
    except ImportError as e:
        raise RuntimeError("Install opentelemetry-api to use AgentLedger OTEL propagation") from e

def inject(carrier:MutableMapping[str,str], context=None)->MutableMapping[str,str]:
    _,propagate=_otel(); propagate.inject(carrier, context=context); return carrier

def extract(carrier:MutableMapping[str,str]):
    _,propagate=_otel(); return propagate.extract(carrier)

def causal_from_current(run_id:str, *, step_id=None, tool_call_id=None, model_call_id=None)->CausalContext:
    trace,_=_otel(); sc=trace.get_current_span().get_span_context()
    if not getattr(sc,"is_valid",False):
        return CausalContext(run_id=run_id,step_id=step_id,tool_call_id=tool_call_id,model_call_id=model_call_id)
    return CausalContext(run_id=run_id,step_id=step_id,trace_id=f"{sc.trace_id:032x}",span_id=f"{sc.span_id:016x}",tool_call_id=tool_call_id,model_call_id=model_call_id)

def bind_span(span, causal:CausalContext):
    for k,v in causal.attributes().items(): span.set_attribute(k,v)
    return span

def child_carrier(causal:CausalContext, carrier=None):
    carrier={} if carrier is None else carrier
    inject(carrier)
    carrier["x-agentledger-run-id"]=causal.run_id
    if causal.step_id: carrier["x-agentledger-step-id"]=causal.step_id
    return carrier
