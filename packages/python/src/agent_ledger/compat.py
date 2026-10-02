"""Versioned capability discovery and compatibility checks for long-lived AgentLedger evidence."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

RUNTIME_CONTRACT = "agentledger.runtime.v1"
EVIDENCE_BUNDLE_VERSION = "agentledger.evidence.bundle/1"
MANIFEST_VERSION = "agent-ledger-run-manifest/1"

@dataclass(frozen=True)
class Capabilities:
    runtime_contract: str = RUNTIME_CONTRACT
    evidence_bundle_versions: tuple[str,...] = (EVIDENCE_BUNDLE_VERSION,)
    manifest_versions: tuple[str,...] = (MANIFEST_VERSION,)
    canonicalization: tuple[str,...] = ("RFC8785",)
    signature_algorithms: tuple[str,...] = ("Ed25519",)
    features: tuple[str,...] = (
        "effects.unknown-reconciliation","evidence.merkle-proof","evidence.portable-bundle",
        "policy.simulation","replay.divergence","otel.causal-context","budgets","cancellation"
    )
    def to_dict(self): return asdict(self)

def capabilities()->dict: return Capabilities().to_dict()

def require_supported(*, bundle_version:str|None=None, manifest_version:str|None=None)->None:
    c=Capabilities()
    if bundle_version and bundle_version not in c.evidence_bundle_versions: raise ValueError(f"unsupported evidence bundle version: {bundle_version}")
    if manifest_version and manifest_version not in c.manifest_versions: raise ValueError(f"unsupported manifest version: {manifest_version}")
