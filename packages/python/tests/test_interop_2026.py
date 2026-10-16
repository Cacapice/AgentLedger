import json
from pathlib import Path
from agent_ledger.jcs import canonicalize
from agent_ledger.otlp_export import event_to_otlp
from agent_ledger.signing import generate_keypair
from agent_ledger.signed_envelope import make_envelope, verify_envelope

def test_shared_jcs_vectors():
    vectors = json.loads((Path(__file__).resolve().parents[3] / "tests/interop/jcs_vectors.json").read_text())
    for v in vectors: assert canonicalize(v["input"]) == v["canonical"]

def test_signed_envelope_and_tamper():
    private, public = generate_keypair()
    env = make_envelope({"event_id": "a"}, private, public)
    assert verify_envelope(env, public)
    env["payload"]["event_id"] = "b"
    assert not verify_envelope(env, public)

def test_otlp_metadata_only():
    payload = event_to_otlp({"event_id": "1", "tool_inputs": "SECRET", "action_type": "run"})
    assert "SECRET" not in json.dumps(payload)
    assert payload["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]["body"]["stringValue"] == "agentledger.audit"
