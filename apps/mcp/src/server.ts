#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { AuditClient } from "@agent-ledger/sdk";

const baseUrl = process.env.AGENT_LEDGER_URL;
const apiKey = process.env.AGENT_LEDGER_API_KEY;
const client = baseUrl && apiKey ? new AuditClient({baseUrl, apiKey}) : null;

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value as object).sort().map(k => `${JSON.stringify(k)}:${stable((value as Record<string,unknown>)[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function digest(value: unknown): string { return createHash("sha256").update(stable(value)).digest("hex"); }

async function verifyFile(path: string) {
  const text = await readFile(path, "utf8");
  let previous: string | null = null;
  let chainId: string | null = null;
  let count = 0;
  for (const [index,line] of text.split(/\r?\n/).entries()) {
    if (!line.trim()) continue;
    count++;
    const event = JSON.parse(line);
    chainId ??= event.chain_id;
    if (event.chain_id !== chainId) return {valid:false,line:index+1,reason:"chain_id changed",events:count};
    if (event.sequence_number !== count) return {valid:false,line:index+1,reason:"sequence_number mismatch",events:count};
    if ((event.prev_event_hash ?? null) !== previous) return {valid:false,line:index+1,reason:"prev_event_hash mismatch",events:count};
    const {event_hash,...rest}=event;
    const expected=digest(rest);
    if (event_hash !== expected) return {valid:false,line:index+1,reason:"event_hash mismatch",events:count};
    previous=event_hash;
  }
  return {valid:true,events:count,chain_id:chainId,head_hash:previous};
}

const server = new McpServer({name:"agent-ledger",version:"0.3.0"});
server.tool("audit_record","Record a consequential agent action in the hosted Agent Ledger",{
  agent_id:z.string(),action_type:z.string(),tool_name:z.string(),execution_status:z.enum(["SUCCESS","FAILED","BLOCKED_BY_POLICY","CANCELLED"]),input_parameters:z.record(z.unknown()).optional(),output_summary:z.record(z.unknown()).optional(),trace_id:z.string().optional(),session_id:z.string().optional()
},async args=>{
  if(!client) return {content:[{type:"text",text:"AGENT_LEDGER_URL and AGENT_LEDGER_API_KEY are required"}],isError:true};
  const result=await client.record(args);
  return {content:[{type:"text",text:JSON.stringify(result,null,2)}]};
});
server.tool("audit_get_receipt","Retrieve and verify a hosted Agent Ledger action receipt",{receipt_id:z.string()},async({receipt_id})=>{
  if(!client) return {content:[{type:"text",text:"AGENT_LEDGER_URL and AGENT_LEDGER_API_KEY are required"}],isError:true};
  return {content:[{type:"text",text:JSON.stringify(await client.receipt(receipt_id),null,2)}]};
});
server.tool("audit_check_policy","Evaluate a simple amount threshold before a consequential action",{amount:z.number(),approval_over:z.number().optional(),deny_over:z.number().optional()},async({amount,approval_over,deny_over})=>{
  const decision=deny_over!==undefined&&amount>deny_over?"DENY":approval_over!==undefined&&amount>approval_over?"REQUIRE_APPROVAL":"ALLOW";
  return {content:[{type:"text",text:JSON.stringify({decision,amount,approval_over,deny_over})}]};
});
server.tool("audit_usage","Read current tenant usage from Agent Ledger",{},async()=>{
  if(!client) return {content:[{type:"text",text:"AGENT_LEDGER_URL and AGENT_LEDGER_API_KEY are required"}],isError:true};
  return {content:[{type:"text",text:JSON.stringify(await client.usage(),null,2)}]};
});
server.tool("audit_verify_file","Verify a local Agent Ledger JSONL hash chain",{path:z.string()},async({path})=>({content:[{type:"text",text:JSON.stringify(await verifyFile(path),null,2)}]}));

await server.connect(new StdioServerTransport());
