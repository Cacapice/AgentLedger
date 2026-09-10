import { AuditClient } from '@agent-ledger/sdk';
const ledger = new AuditClient({baseUrl: process.env.AGENT_LEDGER_URL, apiKey: process.env.AGENT_LEDGER_API_KEY});
console.log(await ledger.record({agent_id:'research-agent',action_type:'TOOL_CALL',tool_name:'search',execution_status:'SUCCESS',input_parameters:{query:'agent governance'}}));
