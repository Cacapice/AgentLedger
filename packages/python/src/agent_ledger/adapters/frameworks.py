"""Dependency-free facades for common agent frameworks.
Framework-specific packages can call these hooks without making AgentLedger own planning.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
@dataclass
class RuntimeAdapter:
    framework:str; run_store:Any; effect_ledger:Any
    def wrap_tool(self,name:str,fn:Callable[...,Any],*,run_id:str,idempotency_key:Callable[...,str]):
        def wrapped(*args,**kwargs):
            req={'args':args,'kwargs':kwargs}; rec=self.effect_ledger.propose(run_id=run_id,tool_name=name,idempotency_key=idempotency_key(*args,**kwargs),request=req)
            if rec.status=='COMMITTED': return {'agentledger_effect':rec.effect_id,'deduplicated':True}
            rec=self.effect_ledger.transition(rec.effect_id,'AUTHORIZED'); rec=self.effect_ledger.transition(rec.effect_id,'ATTEMPTED')
            try:
                out=fn(*args,**kwargs); self.effect_ledger.transition(rec.effect_id,'COMMITTED',response=out); return out
            except Exception as e:
                self.effect_ledger.transition(rec.effect_id,'UNKNOWN',metadata={'error':str(e)}); raise
        return wrapped

def langgraph(run_store,effect_ledger): return RuntimeAdapter('langgraph',run_store,effect_ledger)
def langchain(run_store,effect_ledger): return RuntimeAdapter('langchain',run_store,effect_ledger)
def crewai(run_store,effect_ledger): return RuntimeAdapter('crewai',run_store,effect_ledger)
def autogen(run_store,effect_ledger): return RuntimeAdapter('autogen',run_store,effect_ledger)
def openai_agents(run_store,effect_ledger): return RuntimeAdapter('openai-agents',run_store,effect_ledger)
def llamaindex(run_store,effect_ledger): return RuntimeAdapter('llamaindex',run_store,effect_ledger)
def semantic_kernel(run_store,effect_ledger): return RuntimeAdapter('semantic-kernel',run_store,effect_ledger)
