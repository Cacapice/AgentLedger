"""Adapter certification and deterministic fault injection."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json, uuid
from typing import Any

class InjectedFailure(RuntimeError): pass
class CorruptBlob(RuntimeError): pass

class FaultInjectingStateStore:
    def __init__(self, inner, *, fail_put_calls=()): self.inner=inner; self.fail=set(fail_put_calls); self.n=0
    def get(self,*a,**k): return self.inner.get(*a,**k)
    def put(self,*a,**k):
        self.n+=1
        if self.n in self.fail: raise InjectedFailure(f'put failure #{self.n}')
        return self.inner.put(*a,**k)
    def delete(self,*a,**k): return self.inner.delete(*a,**k)

class VerifyingBlobStore:
    """Checks content-addressed refs on read; catches corrupt/truncated object-store reads."""
    def __init__(self,inner): self.inner=inner
    def put(self,data): return self.inner.put(data)
    def get(self,ref):
        data=self.inner.get(ref); expected=None
        if ref.startswith('sha256:'): expected=ref.split(':',1)[1]
        elif '#sha256=' in ref: expected=ref.rsplit('#sha256=',1)[1]
        if expected and hashlib.sha256(data).hexdigest()!=expected: raise CorruptBlob(ref)
        return data

class CorruptingBlobStore:
    def __init__(self,inner): self.inner=inner
    def put(self,data): return self.inner.put(data)
    def get(self,ref):
        data=self.inner.get(ref); return (data[:-1]+bytes([data[-1]^1])) if data else b'x'

@dataclass
class Check: name:str; passed:bool; detail:str=''
@dataclass
class CertificationReport:
    adapter:str; checks:list[Check]
    @property
    def certified(self): return all(x.passed for x in self.checks)
    def to_json(self): return json.dumps({'adapter':self.adapter,'certified':self.certified,'checks':[asdict(x) for x in self.checks]},sort_keys=True,indent=2)

def certify_state_store(factory, adapter='state-store'):
    checks=[]; s=factory(); ns='cert-'+uuid.uuid4().hex
    try:
        r=s.put(ns,'k',{'v':1},expected_revision=0); checks.append(Check('create-cas',r==1))
        try: s.put(ns,'k',{'v':2},expected_revision=0); checks.append(Check('stale-write-rejected',False))
        except Exception: checks.append(Check('stale-write-rejected',True))
        r=s.put(ns,'k',{'v':2},expected_revision=1); checks.append(Check('update-cas',r==2 and s.get(ns,'k')['v']==2))
        s.delete(ns,'k'); checks.append(Check('delete',s.get(ns,'k') is None))
    except Exception as e: checks.append(Check('unexpected-error',False,str(e)))
    return CertificationReport(adapter,checks)

def certify_blob_store(factory, adapter='blob-store'):
    checks=[]; b=factory(); data=b'agentledger-certification-evidence'; ref=b.put(data)
    try: checks.append(Check('round-trip',b.get(ref)==data))
    except Exception as e: checks.append(Check('round-trip',False,str(e)))
    try:
        VerifyingBlobStore(CorruptingBlobStore(b)).get(ref); checks.append(Check('corruption-detected',False))
    except CorruptBlob: checks.append(Check('corruption-detected',True))
    return CertificationReport(adapter,checks)
