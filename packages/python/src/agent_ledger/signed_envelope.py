"""Portable signed evidence envelope with external public-key verification."""
from __future__ import annotations
import base64
from typing import Any
from .signing import sign_evidence, verify_evidence

def make_envelope(payload: Any, private_key: bytes, public_key: bytes) -> dict[str, Any]:
    return {"envelope_version": "agent-ledger-signed-evidence/1", "payload": payload,
            "signature": sign_evidence(payload, private_key),
            "public_key_base64": base64.b64encode(public_key).decode("ascii")}

def verify_envelope(envelope: dict[str, Any], trusted_public_key: bytes) -> bool:
    """Require caller-supplied trusted key: embedded keys are never trust anchors."""
    if envelope.get("envelope_version") != "agent-ledger-signed-evidence/1": return False
    if envelope.get("public_key_base64") != base64.b64encode(trusted_public_key).decode("ascii"): return False
    return verify_evidence(envelope["payload"], envelope["signature"], trusted_public_key)
