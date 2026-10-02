"""CrewAI native tool-boundary pattern."""
from agent_ledger.runtime import DurableRunStore
from agent_ledger.effects import EffectLedger
from agent_ledger.adapters.frameworks import crewai
from crewai.tools import tool
import tempfile,pathlib
root=pathlib.Path(tempfile.mkdtemp()); runs=DurableRunStore(root/'runs.json'); effects=EffectLedger(root/'effects.json'); run=runs.create('demo'); adapter=crewai(runs,effects)
def write_crm(contact:str): return f'updated:{contact}'
safe=adapter.wrap_tool('write_crm',write_crm,run_id=run.run_id,idempotency_key=lambda contact:f'crm:{contact}')
@tool('update_crm')
def update_crm(contact:str)->str: return safe(contact)
print(update_crm)
