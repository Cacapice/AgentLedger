from __future__ import annotations
import json, os, threading, uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from .core import sha256_hex
EffectStatus=Literal['PROPOSED','AUTHORIZED','ATTEMPTED','COMMITTED','FAILED','UNKNOWN','CANCELLED']
_ALLOWED={'PROPOSED':{'AUTHORIZED','CANCELLED'},'AUTHORIZED':{'ATTEMPTED','CANCELLED'},'ATTEMPTED':{'COMMITTED','FAILED','UNKNOWN'},'UNKNOWN':{'COMMITTED','FAILED'},'COMMITTED':set(),'FAILED':set(),'CANCELLED':set()}
def _now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
class EffectTransitionError(RuntimeError): pass
class EffectConflictError(RuntimeError): pass
@dataclass
class EffectRecord:
    effect_id:str; run_id:str; tool_name:str; idempotency_key:str; request_hash:str; status:EffectStatus='PROPOSED'; response_hash:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); updated_at:str=field(default_factory=_now)
class EffectLedger:
    """Persistent side-effect state machine. UNKNOWN is explicit after an ambiguous external write."""
    def __init__(self,path): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self._lock=threading.RLock()
    def _load(self): return [] if not self.path.exists() else json.loads(self.path.read_text(encoding='utf-8'))
    def _save(self,rows):
        tmp=self.path.with_suffix(self.path.suffix+'.tmp'); tmp.write_text(json.dumps(rows,sort_keys=True,separators=(',',':')),encoding='utf-8'); os.replace(tmp,self.path)
    def propose(self,*,run_id,tool_name,idempotency_key,request,metadata=None):
        with self._lock:
            rows=self._load(); rh=sha256_hex(request)
            for row in rows:
                if row['idempotency_key']==idempotency_key:
                    if row['request_hash']!=rh: raise EffectConflictError('idempotency key reused with different request')
                    return EffectRecord(**row)
            rec=EffectRecord(str(uuid.uuid4()),run_id,tool_name,idempotency_key,rh,metadata=metadata or {}); rows.append(asdict(rec)); self._save(rows); return rec
    def transition(self,effect_id,status:EffectStatus,*,response=None,metadata=None):
        with self._lock:
            rows=self._load()
            for i,row in enumerate(rows):
                if row['effect_id']==effect_id:
                    if status not in _ALLOWED[row['status']]: raise EffectTransitionError(f"invalid effect transition {row['status']} -> {status}")
                    row['status']=status; row['updated_at']=_now()
                    if response is not None: row['response_hash']=sha256_hex(response)
                    if metadata: row['metadata']={**row.get('metadata',{}),**metadata}
                    rows[i]=row; self._save(rows); return EffectRecord(**row)
            raise KeyError(effect_id)
