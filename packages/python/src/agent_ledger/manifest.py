from __future__ import annotations
import base64, hashlib
from dataclasses import dataclass, asdict
from typing import Any
from .jcs import canonicalize_bytes
from .signing import key_fingerprint, _require, Ed25519PrivateKey, Ed25519PublicKey, serialization

def _h(tag:bytes,data:bytes)->bytes: return hashlib.sha256(tag+data).digest()
def leaf_hash(value:Any)->bytes: return _h(b'\x00',canonicalize_bytes(value))
def merkle_root(values:list[Any])->str:
    if not values: return hashlib.sha256(b'').hexdigest()
    level=[leaf_hash(v) for v in values]
    while len(level)>1:
        if len(level)%2: level.append(level[-1])
        level=[_h(b'\x01',level[i]+level[i+1]) for i in range(0,len(level),2)]
    return level[0].hex()

def build_run_manifest(*,run_id:str,events:list[Any],effects:list[Any],metadata:dict[str,Any]|None=None)->dict[str,Any]:
    return {'manifest_version':'agent-ledger-run-manifest/1','canonicalization':'RFC8785','hash':'SHA-256','run_id':run_id,'event_count':len(events),'event_root':merkle_root(events),'effect_count':len(effects),'effect_root':merkle_root(effects),'metadata':metadata or {}}
def sign_manifest(manifest:dict[str,Any],private_key:bytes)->dict[str,Any]:
    _require(); key=Ed25519PrivateKey.from_private_bytes(private_key); pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    return {**manifest,'signature':{'algorithm':'Ed25519','key_fingerprint':key_fingerprint(pub),'value':base64.b64encode(key.sign(canonicalize_bytes(manifest))).decode()}}
def verify_manifest(signed:dict[str,Any],public_key:bytes)->bool:
    _require(); sig=signed.get('signature',{}); body={k:v for k,v in signed.items() if k!='signature'}
    if sig.get('key_fingerprint')!=key_fingerprint(public_key): return False
    try: Ed25519PublicKey.from_public_bytes(public_key).verify(base64.b64decode(sig['value']),canonicalize_bytes(body)); return True
    except Exception: return False
