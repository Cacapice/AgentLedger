"""Failure-path regression tests for evidence key lifecycle."""
import pytest

pytest.importorskip("cryptography")
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from agent_ledger.key_registry import KeyRegistry
from agent_ledger.signed_envelope import make_envelope

def _keypair():
    key = Ed25519PrivateKey.generate()
    return (key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()),
            key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))

def test_tampering_and_revocation_and_rotation():
    secret, public = _keypair()
    replacement_secret, replacement_public = _keypair()
    registry = KeyRegistry()
    registry.add("initial", public)
    original = make_envelope({"action": "charge", "amount": 3}, secret, public)
    assert registry.verify(original, "initial")
    changed = {**original, "payload": {"action": "charge", "amount": 300}}
    assert not registry.verify(changed, "initial")
    registry.rotate("initial", "replacement", replacement_public)
    assert not registry.verify(original, "initial")
    replacement = make_envelope({"action": "charge", "amount": 3}, replacement_secret, replacement_public)
    assert registry.verify(replacement, "replacement")
    registry.revoke("replacement")
    assert not registry.verify(replacement, "replacement")
