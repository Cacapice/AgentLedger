"""W3C trace-context friendly causal identifiers for evidence correlation."""
from __future__ import annotations
from dataclasses import dataclass,asdict
@dataclass(frozen=True)
class CausalContext:
    run_id:str; step_id:str|None=None; trace_id:str|None=None; span_id:str|None=None; parent_span_id:str|None=None; tool_call_id:str|None=None; model_call_id:str|None=None; causal_token:str|None=None
    def attributes(self): return {f'agentledger.{k}':v for k,v in asdict(self).items() if v is not None}
