"""LangGraph-native pattern. pip install langgraph; set your model/tooling as appropriate."""
from agent_ledger.runtime import DurableRunStore
from agent_ledger.effects import EffectLedger
from agent_ledger.adapters.frameworks import langgraph
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import tempfile, pathlib
class State(TypedDict): message:str
root=pathlib.Path(tempfile.mkdtemp()); runs=DurableRunStore(root/'runs.json'); effects=EffectLedger(root/'effects.json'); run=runs.create('demo')
adapter=langgraph(runs,effects)
def external_send(message:str): return {'sent':message}
safe_send=adapter.wrap_tool('send',external_send,run_id=run.run_id,idempotency_key=lambda message:f'send:{message}')
def node(state:State): safe_send(state['message']); return state
g=StateGraph(State); g.add_node('send',node); g.add_edge(START,'send'); g.add_edge('send',END)
print(g.compile().invoke({'message':'hello'}))
