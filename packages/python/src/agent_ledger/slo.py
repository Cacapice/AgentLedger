"""Evidence-derived reliability/SLO scorecards."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any

def evidence_slo(*,effects,divergences=(),lease_events=()):
    total=len(effects); unknown=sum(e.get("status")=="UNKNOWN" for e in effects); failed=sum(e.get("status")=="FAILED" for e in effects)
    return {"effect_count":total,"committed_rate":(sum(e.get("status")=="COMMITTED" for e in effects)/total if total else 1.0),"unknown_rate":unknown/total if total else 0.0,"failed_rate":failed/total if total else 0.0,"replay_divergence_count":len(divergences),"lease_event_count":len(lease_events)}

DEFAULT_OBJECTIVES={"committed_rate":0.999,"unknown_rate":0.001,"failed_rate":0.001,"replay_divergence_count":0}

def scorecard(*,effects,divergences=(),lease_events=(),objectives=None,window="all",dimensions=None)->dict[str,Any]:
    metrics=evidence_slo(effects=effects,divergences=divergences,lease_events=lease_events)
    objectives={**DEFAULT_OBJECTIVES,**(objectives or {})}; checks={}
    for k,target in objectives.items():
        actual=metrics.get(k)
        if actual is None: continue
        good=(actual>=target) if k=="committed_rate" else (actual<=target)
        checks[k]={"actual":actual,"target":target,"met":good}
    met=sum(c["met"] for c in checks.values()); total=len(checks)
    return {"window":window,"dimensions":dimensions or {},"metrics":metrics,"objectives":checks,
            "objectives_met":met,"objectives_total":total,"healthy":met==total,
            "score":met/total if total else 1.0}

def grouped_scorecards(effects, *, group_by=("agent_id","agent_version","provider"), objectives=None):
    groups={}
    for e in effects:
        key=tuple(e.get(k) for k in group_by); groups.setdefault(key,[]).append(e)
    return [{"group":dict(zip(group_by,key)),**scorecard(effects=vals,objectives=objectives,dimensions=dict(zip(group_by,key)))} for key,vals in groups.items()]
