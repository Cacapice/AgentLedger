from __future__ import annotations
import json, os, threading, uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

def _now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
RunStatus=Literal['PENDING','RUNNING','WAITING','SUCCEEDED','FAILED','CANCELLED']

@dataclass
class RunState:
    run_id: str; status: RunStatus='PENDING'; step: str|None=None; checkpoint: Any=None
    lease_token: str|None=None; lease_owner: str|None=None; updated_at: str=field(default_factory=_now); revision: int=0

class StaleLeaseError(RuntimeError): pass

class DurableRunStore:
    """Crash-recoverable file store with fencing tokens and atomic replace writes."""
    def __init__(self,path): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self._lock=threading.RLock()
    def _load(self):
        if not self.path.exists(): return {}
        return json.loads(self.path.read_text(encoding='utf-8'))
    def _save(self,data):
        tmp=self.path.with_suffix(self.path.suffix+'.tmp'); tmp.write_text(json.dumps(data,sort_keys=True,separators=(',',':')),encoding='utf-8'); os.replace(tmp,self.path)
    def create(self,run_id=None):
        with self._lock:
            data=self._load(); rid=run_id or str(uuid.uuid4())
            if rid in data: raise ValueError(f'run already exists: {rid}')
            state=RunState(rid); data[rid]=asdict(state); self._save(data); return state
    def get(self,run_id):
        row=self._load().get(run_id)
        if row is None: raise KeyError(run_id)
        return RunState(**row)
    def acquire(self,run_id,owner):
        with self._lock:
            data=self._load(); state=RunState(**data[run_id]); state.lease_owner=owner; state.lease_token=str(uuid.uuid4()); state.status='RUNNING'; state.revision+=1; state.updated_at=_now(); data[run_id]=asdict(state); self._save(data); return state
    def checkpoint(self,run_id,lease_token,*,step,checkpoint,status='RUNNING'):
        with self._lock:
            data=self._load(); state=RunState(**data[run_id])
            if not state.lease_token or state.lease_token != lease_token: raise StaleLeaseError('lease/fencing token is stale')
            state.step=step; state.checkpoint=checkpoint; state.status=status; state.revision+=1; state.updated_at=_now(); data[run_id]=asdict(state); self._save(data); return state
    def finish(self,run_id,lease_token,status='SUCCEEDED'):
        if status not in ('SUCCEEDED','FAILED','CANCELLED'): raise ValueError('invalid terminal status')
        state=self.checkpoint(run_id,lease_token,step=self.get(run_id).step,checkpoint=self.get(run_id).checkpoint,status=status)
        return state
