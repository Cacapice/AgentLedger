"""Selective disclosure packets backed by signed run roots."""
from __future__ import annotations
from typing import Any
from .manifest import merkle_proof, verify_merkle_proof, verify_manifest

def disclose(values:list[Any], index:int, *, kind:str, signed_manifest:dict[str,Any])->dict[str,Any]:
    if kind not in ("event","effect"): raise ValueError("kind must be event or effect")
    proof=merkle_proof(values,index)
    expected=signed_manifest[f"{kind}_root"]
    if proof["root"]!=expected: raise ValueError("values do not match signed manifest root")
    return {"kind":kind,"value":values[index],"proof":proof,"manifest":signed_manifest}

def verify_disclosure(packet:dict[str,Any], *, public_key:bytes|None=None)->bool:
    kind=packet.get("kind")
    if kind not in ("event","effect"): return False
    manifest=packet.get("manifest",{})
    if packet.get("proof",{}).get("root")!=manifest.get(f"{kind}_root"): return False
    if not verify_merkle_proof(packet.get("value"),packet.get("proof",{})): return False
    if "signature" in manifest:
        return bool(public_key and verify_manifest(manifest,public_key))
    return True
