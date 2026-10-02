"""Provider-neutral reconciliation registry for ambiguous external effects."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
@dataclass(frozen=True)
class ReconciliationResult:
    status:str; evidence:dict[str,Any]; provider:str
class ReconcilerRegistry:
    def __init__(self): self._items={}
    def register(self,provider:str,fn:Callable[[dict[str,Any]],ReconciliationResult]): self._items[provider]=fn; return fn
    def reconcile(self,provider:str,effect:dict[str,Any])->ReconciliationResult:
        if effect.get('status')!='UNKNOWN': raise ValueError('only UNKNOWN effects require reconciliation')
        if provider not in self._items: raise KeyError(f'no reconciler registered: {provider}')
        r=self._items[provider](effect)
        if r.status not in ('COMMITTED','FAILED','UNKNOWN'): raise ValueError('reconciler returned invalid status')
        return r
