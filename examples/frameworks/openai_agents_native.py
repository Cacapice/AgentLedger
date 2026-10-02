"""OpenAI Agents SDK pattern: wrap the side-effecting function before exposing it as a tool."""
from agent_ledger.runtime import DurableRunStore
from agent_ledger.effects import EffectLedger
from agent_ledger.adapters.frameworks import openai_agents
from agents import Agent, Runner, function_tool
import tempfile,pathlib,asyncio
root=pathlib.Path(tempfile.mkdtemp()); runs=DurableRunStore(root/'runs.json'); effects=EffectLedger(root/'effects.json'); run=runs.create('demo'); adapter=openai_agents(runs,effects)
def create_ticket(title:str): return {'ticket_id':'T-1','title':title}
safe=adapter.wrap_tool('create_ticket',create_ticket,run_id=run.run_id,idempotency_key=lambda title:f'ticket:{title}')
@function_tool
def create_ticket_tool(title:str)->str: return str(safe(title))
agent=Agent(name='Support',instructions='Create one ticket when asked.',tools=[create_ticket_tool])
async def main(): print(await Runner.run(agent,'Create a ticket titled demo'))
if __name__=='__main__': asyncio.run(main())
