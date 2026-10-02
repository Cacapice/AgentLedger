"""Side-effect-free policy simulation over recorded decisions/actions."""
from __future__ import annotations
from dataclasses import dataclass,asdict
@dataclass
class PolicyDelta:
    index:int; recorded:str|None; simulated:str; changed:bool; reason:str

def simulate(records, engine, *, amount_field='amount'):
    out=[]
    for i,r in enumerate(records):
        d=engine.evaluate(amount=r.get(amount_field)); recorded=r.get('policy_result') or r.get('decision')
        out.append(PolicyDelta(i,recorded,d.decision,recorded is not None and recorded!=d.decision,d.reason))
    return {'evaluated':len(out),'changed':sum(x.changed for x in out),'deltas':[asdict(x) for x in out]}
