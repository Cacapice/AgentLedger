"""Loss-minimizing mapping of APE events to OpenTelemetry log attributes.

Not an OTLP exporter or a certification of OpenTelemetry GenAI semconv.
Raw payloads are deliberately excluded from telemetry by default.
"""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any
import re

_TRACEPARENT = re.compile(r'^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$')


def parse_traceparent(value: str) -> dict[str, str]:
    """Validate W3C traceparent version 00, rejecting invalid all-zero IDs."""
    match = _TRACEPARENT.fullmatch(value)
    if not match or int(match[1], 16) == 0 or int(match[2], 16) == 0:
        raise ValueError('invalid W3C traceparent version 00')
    return {'trace_id': match[1], 'span_id': match[2], 'trace_flags': match[3]}


def event_to_otel_attributes(event: Mapping[str, Any]) -> dict[str, str]:
    """Map non-sensitive event metadata; do not serialize prompts or outcomes."""
    if not event.get('event_id') or not event.get('agent_id'):
        raise ValueError('event_id and agent_id are required')
    attrs = {
        'agentledger.event.id': str(event['event_id']),
        'agentledger.schema.version': str(event.get('schema_version', 'ape/1.0')),
        'gen_ai.agent.id': str(event['agent_id']),
    }
    for source, target in (
        ('run_id', 'agentledger.run.id'),
        ('action', 'agentledger.action'),
        ('policy_id', 'agentledger.policy.id'),
        ('agent_version', 'agentledger.agent.version'),
    ):
        if event.get(source) is not None:
            attrs[target] = str(event[source])
    # Custom agentledger.* attributes are not official OTel semantic conventions.
    return attrs
