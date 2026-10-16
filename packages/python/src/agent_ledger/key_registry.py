"""Explicit trust registry for Ed25519 evidence keys, with revocation.

Revocation is evaluated at verification time; archival verification requires
separate trusted timestamp evidence and a documented historical trust policy.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .signed_envelope import verify_envelope

@dataclass
class KeyRegistry:
    trusted: dict[str, bytes] = field(default_factory=dict)
    revoked: set[str] = field(default_factory=set)

    def add(self, key_id: str, public_key: bytes) -> None:
        if not key_id or len(public_key) != 32 or key_id in self.revoked:
            raise ValueError("invalid or revoked key")
        self.trusted[key_id] = public_key

    def revoke(self, key_id: str) -> None:
        self.revoked.add(key_id)
        self.trusted.pop(key_id, None)

    def rotate(self, old_id: str, new_id: str, new_key: bytes) -> None:
        if old_id not in self.trusted:
            raise ValueError("old key is not trusted")
        self.add(new_id, new_key)
        self.revoke(old_id)

    def verify(self, envelope: dict[str, Any], key_id: str) -> bool:
        if key_id in self.revoked or key_id not in self.trusted:
            return False
        return verify_envelope(envelope, self.trusted[key_id])
