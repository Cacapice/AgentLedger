"""OTLP/HTTP JSON exporter for AgentLedger audit events (logs signal)."""
from __future__ import annotations
import json, os, time, urllib.request, urllib.error
from typing import Any


def _attribute(k: str, v: Any) -> dict[str, Any]:
    if isinstance(v, bool): value = {"boolValue": v}
    elif isinstance(v, int): value = {"intValue": str(v)}
    elif isinstance(v, float): value = {"doubleValue": v}
    else: value = {"stringValue": str(v)}
    return {"key": k, "value": value}


def event_to_otlp(event: dict[str, Any], *, service_name: str = "agent-ledger") -> dict[str, Any]:
    """Export metadata only; omit inputs, outputs and sensitive payloads."""
    fields = ("event_id", "agent_id", "action_type", "tool_name", "execution_status", "payload_hash", "prev_event_hash")
    attrs = [_attribute("agentledger." + k, event[k]) for k in fields if event.get(k) is not None]
    record: dict[str, Any] = {"timeUnixNano": str(time.time_ns()), "severityNumber": 9,
        "body": {"stringValue": "agentledger.audit"}, "attributes": attrs}
    trace = event.get("trace_id"); span = event.get("span_id")
    if isinstance(trace, str) and len(trace) == 32 and int(trace, 16): record["traceId"] = trace.lower()
    if isinstance(span, str) and len(span) == 16 and int(span, 16): record["spanId"] = span.lower()
    return {"resourceLogs": [{"resource": {"attributes": [_attribute("service.name", service_name)]},
        "scopeLogs": [{"scope": {"name": "agent-ledger", "version": "0.9.2"}, "logRecords": [record]}]}]}


def export_otlp_log(event: dict[str, Any], endpoint: str | None = None, *, timeout: float = 10.0, headers: dict[str, str] | None = None) -> None:
    """Send audit event with transient-error retry and partial-rejection detection."""
    from .otlp_transport import export
    export("logs", event_to_otlp(event), endpoint=endpoint, timeout=timeout, headers=headers)
