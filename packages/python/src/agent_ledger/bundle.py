"""Portable, offline-verifiable run evidence bundles."""
from __future__ import annotations
import json, zipfile
from pathlib import Path
from typing import Any
from .compat import EVIDENCE_BUNDLE_VERSION, require_supported
from .jcs import canonicalize_bytes
from .manifest import build_run_manifest, sign_manifest, verify_manifest, merkle_root

def export_bundle(path, *, run_id:str, events:list[Any], effects:list[Any], metadata=None, private_key:bytes|None=None)->Path:
    p=Path(path); manifest=build_run_manifest(run_id=run_id,events=events,effects=effects,metadata=metadata)
    if private_key: manifest=sign_manifest(manifest,private_key)
    header={'bundle_version':EVIDENCE_BUNDLE_VERSION,'run_id':run_id,'manifest':manifest}
    with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('bundle.json',canonicalize_bytes(header)); z.writestr('events.json',canonicalize_bytes(events)); z.writestr('effects.json',canonicalize_bytes(effects))
    return p

def verify_bundle(path, *, public_key:bytes|None=None)->dict[str,Any]:
    with zipfile.ZipFile(path) as z:
        header=json.loads(z.read('bundle.json')); events=json.loads(z.read('events.json')); effects=json.loads(z.read('effects.json'))
    require_supported(bundle_version=header['bundle_version']); m=header['manifest']
    checks={'run_id':header['run_id']==m['run_id'],'event_count':len(events)==m['event_count'],'effect_count':len(effects)==m['effect_count'],'event_root':merkle_root(events)==m['event_root'],'effect_root':merkle_root(effects)==m['effect_root']}
    if 'signature' in m: checks['signature']=bool(public_key and verify_manifest(m,public_key))
    return {'valid':all(checks.values()),'checks':checks,'manifest':m,'events':events,'effects':effects}
