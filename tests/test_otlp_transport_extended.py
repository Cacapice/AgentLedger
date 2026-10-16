import json
import urllib.error
from unittest.mock import patch
import pytest
from agent_ledger.otlp_transport import export, endpoint_for, export_span, export_counter
from agent_ledger.key_registry import KeyRegistry

class Response:
    status = 200
    def __init__(self, payload=b"{}"): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.payload

def test_all_signals_and_paths(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318/base")
    for signal in ("logs", "traces", "metrics"):
        assert endpoint_for(signal) == "http://collector:4318/base/v1/" + signal
        with patch("urllib.request.urlopen", return_value=Response()) as send:
            export(signal, {})
            assert send.call_args.args[0].full_url.endswith("/v1/" + signal)

def test_transient_retry():
    error = urllib.error.HTTPError("url", 503, "unavailable", {}, None)
    with patch("urllib.request.urlopen", side_effect=[error, Response()]) as send, patch("time.sleep"):
        export("logs", {})
        assert send.call_count == 2

def test_no_retry_partial():
    with patch("urllib.request.urlopen", return_value=Response(b'{"partialSuccess":{"rejectedLogRecords":1}}')) as send:
        with pytest.raises(RuntimeError, match="partial"):
            export("logs", {})
        assert send.call_count == 1

def test_trace_and_metric_payload():
    with patch("urllib.request.urlopen", return_value=Response()) as send:
        export_span("1"*32, "2"*16, "test", 1, 2)
        assert b"resourceSpans" in send.call_args.args[0].data
        export_counter("agentledger.events", 1, 2)
        assert b"resourceMetrics" in send.call_args.args[0].data

def test_registry_rotation_and_revocation():
    registry = KeyRegistry()
    registry.add("old", b"a"*32)
    registry.rotate("old", "new", b"b"*32)
    assert "old" in registry.revoked
    assert "new" in registry.trusted
    assert not registry.verify({}, "old")
