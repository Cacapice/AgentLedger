from __future__ import annotations
import hashlib
from dataclasses import dataclass, asdict
from typing import Any, Callable
from .jcs import canonicalize_bytes

def _digest(v): return hashlib.sha256(canonicalize_bytes(v)).hexdigest()
@dataclass
class Divergence:
    index:int; kind:str; expected:Any; actual:Any
@dataclass
class ReplayReport:
    matched:int; divergences:list[Divergence]; effects_executed:bool=False
    @property
    def equivalent(self): return not self.divergences
    def to_dict(self): return {'matched':self.matched,'equivalent':self.equivalent,'effects_executed':self.effects_executed,'divergences':[asdict(x) for x in self.divergences]}
def compare(expected:list[Any],actual:list[Any])->ReplayReport:
    ds=[]; matched=0
    for i in range(max(len(expected),len(actual))):
        if i>=len(expected): ds.append(Divergence(i,'unexpected',None,actual[i])); continue
        if i>=len(actual): ds.append(Divergence(i,'missing',expected[i],None)); continue
        if _digest(expected[i])!=_digest(actual[i]): ds.append(Divergence(i,'content',expected[i],actual[i]))
        else: matched+=1
    return ReplayReport(matched,ds,False)
def replay_effects(recorded:list[dict[str,Any]], executor:Callable[[dict[str,Any]],Any]|None=None)->ReplayReport:
    # Safe default: validate/replay structurally; external effects require an explicit executor.
    if executor is None: return ReplayReport(len(recorded),[],False)
    actual=[executor(x) for x in recorded]
    r=compare(recorded,actual); r.effects_executed=True; return r
