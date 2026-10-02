"""Forward-compatible cancellation and budget controls at the runtime boundary."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass
class Budget:
    max_cost:float|None=None; max_tokens:int|None=None; cost:float=0.0; tokens:int=0
    def charge(self,*,cost=0.0,tokens=0):
        nc,nt=self.cost+cost,self.tokens+tokens
        if self.max_cost is not None and nc>self.max_cost: raise RuntimeError('cost budget exceeded')
        if self.max_tokens is not None and nt>self.max_tokens: raise RuntimeError('token budget exceeded')
        self.cost,self.tokens=nc,nt
@dataclass
class CancellationToken:
    cancelled:bool=False; reason:str|None=None
    def cancel(self,reason='cancelled'): self.cancelled=True; self.reason=reason
    def check(self):
        if self.cancelled: raise RuntimeError(f'run cancelled: {self.reason}')
