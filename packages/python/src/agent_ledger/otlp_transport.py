"""OTLP/HTTP JSON transport for logs, traces and metrics.

For protobuf and gRPC use the official OpenTelemetry SDK exporters; this
module deliberately implements the OTLP/HTTP JSON transport only.
"""
from __future__ import annotations
import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any

RETRYABLE = frozenset((429, 502, 503, 504))
SIGNALS = frozenset(("logs", "traces", "metrics"))


def endpoint_for(signal: str, base: str | None = None) -> str:
    if signal not in SIGNALS:
        raise ValueError("unsupported OTLP signal")
    override = os.getenv(f"OTEL_EXPORTER_OTLP_{signal.upper()}_ENDPOINT")
    if override:
        return override
    root = base or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or "http://localhost:4318"
    return root.rstrip("/") + "/v1/" + signal


def export(signal: str, payload: dict[str, Any], *, endpoint: str | None = None,
           attempts: int = 4, timeout: float = 10.0,
           headers: dict[str, str] | None = None) -> dict[str, Any]:
    """Send OTLP JSON, retry transient failures with bounded exponential jitter.

    Raise on partial rejection; never retry a partial-success response.
    """
    if attempts < 1:
        raise ValueError("attempts must be positive")
    url = endpoint or endpoint_for(signal)
    data = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
    request = urllib.request.Request(url, data=data, method="POST", headers={
        "Content-Type": "application/json",
        "User-Agent": "AgentLedger-OTLP-Python/0.9.2",
        **(headers or {}),
    })
    for index in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"OTLP unexpected HTTP status {response.status}")
                result = json.loads(response.read() or b"{}")
                partial = result.get("partialSuccess", {})
                rejected = partial.get({"logs": "rejectedLogRecords", "traces": "rejectedSpans", "metrics": "rejectedDataPoints"}[signal], 0)
                if int(rejected):
                    raise RuntimeError(f"OTLP partial rejection: {rejected}")
                return result
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE or index == attempts - 1:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = max(0.0, min(float(retry_after), 30.0)) if retry_after else None
            except ValueError:
                delay = None
        except (urllib.error.URLError, TimeoutError):
            if index == attempts - 1:
                raise
            delay = None
        time.sleep(delay if delay is not None else min(8.0, 0.25 * 2 ** index) * random.uniform(0.5, 1.5))
    raise RuntimeError("unreachable")


def export_log(event: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    from .otlp_export import event_to_otlp
    return export("logs", event_to_otlp(event), **kwargs)


def export_span(trace_id: str, span_id: str, name: str, start_ns: int,
                end_ns: int, **kwargs: Any) -> dict[str, Any]:
    if len(trace_id) != 32 or len(span_id) != 16 or not int(trace_id, 16) or not int(span_id, 16):
        raise ValueError("invalid trace/span identifiers")
    if end_ns < start_ns:
        raise ValueError("span end precedes start")
    payload = {"resourceSpans": [{"resource": {"attributes": []}, "scopeSpans": [{
        "scope": {"name": "agent-ledger"}, "spans": [{"traceId": trace_id, "spanId": span_id,
        "name": name, "startTimeUnixNano": str(start_ns), "endTimeUnixNano": str(end_ns)}]}]}]}
    return export("traces", payload, **kwargs)


def export_counter(name: str, value: int, timestamp_ns: int, **kwargs: Any) -> dict[str, Any]:
    if value < 0:
        raise ValueError("counter must be nonnegative")
    payload = {"resourceMetrics": [{"resource": {"attributes": []}, "scopeMetrics": [{
        "scope": {"name": "agent-ledger"}, "metrics": [{"name": name, "sum": {
        "aggregationTemporality": 2, "isMonotonic": True,
        "dataPoints": [{"asInt": str(value), "timeUnixNano": str(timestamp_ns)}]}}]}]}]}
    return export("metrics", payload, **kwargs)
