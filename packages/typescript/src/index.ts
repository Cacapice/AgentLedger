export type ExecutionStatus = "SUCCESS" | "FAILED" | "BLOCKED_BY_POLICY" | "CANCELLED";

export interface AuditEventInput {
  event_id?: string;
  timestamp?: string;
  source_event_hash?: string | null;
  source_chain_id?: string | null;
  source_sequence_number?: number | null;
  agent_id: string;
  agent_version?: string | null;
  user_principal_id?: string;
  principal_type?: string;
  session_id?: string | null;
  trace_id?: string | null;
  action_type: string;
  tool_name: string;
  resource?: Record<string, unknown> | null;
  model_context?: Record<string, unknown> | null;
  policy_context?: Record<string, unknown> | null;
  input_parameters?: Record<string, unknown>;
  output_summary?: Record<string, unknown>;
  execution_duration_ms?: number;
  execution_status: ExecutionStatus;
  error?: Record<string, unknown> | null;
  redaction?: { applied: boolean; fields: string[] };
}

export interface AuditClientOptions {
  baseUrl: string;
  apiKey: string;
  fetchImpl?: typeof fetch;
}

const sensitive = /authorization|cookie|password|secret|token|api[_-]?key|private[_-]?key|account(_number)?|ssn/i;

export function redact<T>(value: T, path = "$", hits: string[] = []): { value: T; fields: string[] } {
  const walk = (v: unknown, p: string, key?: string): unknown => {
    if (key && sensitive.test(key)) {
      hits.push(p);
      return "[REDACTED]";
    }
    if (Array.isArray(v)) return v.map((x, i) => walk(x, `${p}[${i}]`));
    if (v && typeof v === "object") {
      return Object.fromEntries(Object.entries(v as Record<string, unknown>).map(([k, x]) => [k, walk(x, `${p}.${k}`, k)]));
    }
    if (typeof v === "string" && v.length > 2000) {
      hits.push(p);
      return `${v.slice(0, 2000)}…[TRUNCATED]`;
    }
    return v;
  };
  return { value: walk(value, path) as T, fields: [...new Set(hits)].sort() };
}

export class AuditClient {
  private readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: AuditClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.apiKey = options.apiKey;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async record(event: AuditEventInput): Promise<Record<string, unknown>> {
    const input = redact(event.input_parameters ?? {}, "$.input_parameters");
    const output = redact(event.output_summary ?? {}, "$.output_summary");
    const payload: AuditEventInput = {
      ...event,
      event_id: event.event_id ?? crypto.randomUUID(),
      timestamp: event.timestamp ?? new Date().toISOString(),
      user_principal_id: event.user_principal_id ?? "system",
      principal_type: event.principal_type ?? "SYSTEM",
      input_parameters: input.value,
      output_summary: output.value,
      redaction: { applied: input.fields.length + output.fields.length > 0, fields: [...new Set([...input.fields, ...output.fields])].sort() }
    };
    const response = await this.fetchImpl(`${this.baseUrl}/v1/events`, {
      method: "POST",
      headers: {"content-type": "application/json", "authorization": `Bearer ${this.apiKey}`},
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error(`Agent Ledger ingestion failed (${response.status}): ${await response.text()}`);
    return await response.json() as Record<string, unknown>;
  }

  async recordBatch(events: AuditEventInput[]): Promise<Record<string, unknown>> {
    const response = await this.fetchImpl(`${this.baseUrl}/v1/events/batch`, {
      method: "POST",
      headers: {"content-type": "application/json", "authorization": `Bearer ${this.apiKey}`},
      body: JSON.stringify({events})
    });
    if (!response.ok) throw new Error(`Agent Ledger batch ingestion failed (${response.status}): ${await response.text()}`);
    return await response.json() as Record<string, unknown>;
  }

  async usage(): Promise<Record<string, unknown>> {
    const response = await this.fetchImpl(`${this.baseUrl}/v1/usage`, {headers: {"authorization": `Bearer ${this.apiKey}`}});
    if (!response.ok) throw new Error(`Agent Ledger usage failed (${response.status}): ${await response.text()}`);
    return await response.json() as Record<string, unknown>;
  }
  async receipt(receiptId: string): Promise<Record<string, unknown>> {
    const response = await this.fetchImpl(`${this.baseUrl}/v1/receipts/${encodeURIComponent(receiptId)}`, {headers:{"authorization":`Bearer ${this.apiKey}`}});
    if (!response.ok) throw new Error(`Agent Ledger receipt failed (${response.status}): ${await response.text()}`);
    return await response.json() as Record<string, unknown>;
  }

  async action<T>(name:string, details:{agentId:string; agentVersion?:string; policy?:string; authority?:string; tool?:string}, fn:()=>Promise<T>):Promise<T>{
    const started=Date.now();
    try { const out=await fn(); await this.record({agent_id:details.agentId,agent_version:details.agentVersion,user_principal_id:details.authority??"system",action_type:name,tool_name:details.tool??name,execution_status:"SUCCESS",execution_duration_ms:Date.now()-started,policy_context:details.policy?{policy_id:details.policy,decision:"ALLOWED"}:undefined,output_summary:{result_type:typeof out}}); return out; }
    catch(error){ await this.record({agent_id:details.agentId,agent_version:details.agentVersion,user_principal_id:details.authority??"system",action_type:name,tool_name:details.tool??name,execution_status:"FAILED",execution_duration_ms:Date.now()-started,error:{message:String(error)}}); throw error; }
  }

}

// --- Durable runtime, effect ledger, RFC 8785, manifests and replay ---
export type RunStatus="PENDING"|"RUNNING"|"WAITING"|"SUCCEEDED"|"FAILED"|"CANCELLED";
export interface RunState {run_id:string;status:RunStatus;step?:string;checkpoint?:unknown;lease_token?:string;lease_owner?:string;revision:number;updated_at:string}
export class StaleLeaseError extends Error {}
export class DurableRunStore {
  private runs=new Map<string,RunState>();
  create(runId=crypto.randomUUID()){if(this.runs.has(runId))throw new Error(`run already exists: ${runId}`);const s={run_id:runId,status:"PENDING" as RunStatus,revision:0,updated_at:new Date().toISOString()};this.runs.set(runId,s);return structuredClone(s)}
  get(id:string){const s=this.runs.get(id);if(!s)throw new Error(`unknown run: ${id}`);return structuredClone(s)}
  acquire(id:string,owner:string){const s=this.get(id);s.lease_owner=owner;s.lease_token=crypto.randomUUID();s.status="RUNNING";s.revision++;s.updated_at=new Date().toISOString();this.runs.set(id,s);return structuredClone(s)}
  checkpoint(id:string,token:string,step:string,checkpoint:unknown,status:RunStatus="RUNNING"){const s=this.get(id);if(!s.lease_token||s.lease_token!==token)throw new StaleLeaseError("lease/fencing token is stale");Object.assign(s,{step,checkpoint,status,revision:s.revision+1,updated_at:new Date().toISOString()});this.runs.set(id,s);return structuredClone(s)}
}
export type EffectStatus="PROPOSED"|"AUTHORIZED"|"ATTEMPTED"|"COMMITTED"|"FAILED"|"UNKNOWN"|"CANCELLED";
export interface EffectRecord {effect_id:string;run_id:string;tool_name:string;idempotency_key:string;request_hash:string;status:EffectStatus;response_hash?:string;metadata:Record<string,unknown>;updated_at:string}
const transitions:Record<EffectStatus,EffectStatus[]>={PROPOSED:["AUTHORIZED","CANCELLED"],AUTHORIZED:["ATTEMPTED","CANCELLED"],ATTEMPTED:["COMMITTED","FAILED","UNKNOWN"],UNKNOWN:["COMMITTED","FAILED"],COMMITTED:[],FAILED:[],CANCELLED:[]};
export class EffectLedger {
 private rows:EffectRecord[]=[];
 async propose(x:{run_id:string;tool_name:string;idempotency_key:string;request:unknown;metadata?:Record<string,unknown>}){const request_hash=await sha256Jcs(x.request);const prior=this.rows.find(r=>r.idempotency_key===x.idempotency_key);if(prior){if(prior.request_hash!==request_hash)throw new Error("idempotency key reused with different request");return structuredClone(prior)}const r:EffectRecord={effect_id:crypto.randomUUID(),run_id:x.run_id,tool_name:x.tool_name,idempotency_key:x.idempotency_key,request_hash,status:"PROPOSED",metadata:x.metadata??{},updated_at:new Date().toISOString()};this.rows.push(r);return structuredClone(r)}
 async transition(id:string,status:EffectStatus,response?:unknown,metadata?:Record<string,unknown>){const r=this.rows.find(x=>x.effect_id===id);if(!r)throw new Error(`unknown effect: ${id}`);if(!transitions[r.status].includes(status))throw new Error(`invalid effect transition ${r.status} -> ${status}`);r.status=status;r.updated_at=new Date().toISOString();if(response!==undefined)r.response_hash=await sha256Jcs(response);if(metadata)r.metadata={...r.metadata,...metadata};return structuredClone(r)}
 list(runId?:string){return structuredClone(runId?this.rows.filter(x=>x.run_id===runId):this.rows)}
}
function assertUnicode(s:string){for(let i=0;i<s.length;i++){const c=s.charCodeAt(i);if(c>=0xd800&&c<=0xdbff){const n=s.charCodeAt(++i);if(!(n>=0xdc00&&n<=0xdfff))throw new Error("lone surrogate is not valid I-JSON")}else if(c>=0xdc00&&c<=0xdfff)throw new Error("lone surrogate is not valid I-JSON")}}
export function canonicalizeJcs(v:unknown):string {if(v===null)return"null";if(typeof v==="string"){assertUnicode(v);return JSON.stringify(v)}if(typeof v==="number"){if(!Number.isFinite(v))throw new Error("NaN and Infinity are not valid I-JSON");return JSON.stringify(v)}if(typeof v==="boolean")return v?"true":"false";if(Array.isArray(v))return`[${v.map(canonicalizeJcs).join(",")}]`;if(typeof v==="object"){const o=v as Record<string,unknown>;const ks=Object.keys(o).sort();ks.forEach(assertUnicode);return`{${ks.map(k=>`${JSON.stringify(k)}:${canonicalizeJcs(o[k])}`).join(",")}}`}throw new Error(`unsupported JSON type: ${typeof v}`)}
type Bytes = Uint8Array<ArrayBuffer>;
function ownedBytes(input: Uint8Array): Bytes {
  const out = new Uint8Array(input.byteLength);
  out.set(input);
  return out;
}
async function sha256Bytes(input: Uint8Array): Promise<Bytes> {
  const digest = await crypto.subtle.digest("SHA-256", ownedBytes(input));
  return new Uint8Array(digest);
}
function hex(b: Uint8Array){return [...b].map(x=>x.toString(16).padStart(2,"0")).join("")}
function enc(s:string): Bytes {return ownedBytes(new TextEncoder().encode(s))}
export async function sha256Jcs(v:unknown){return hex(await sha256Bytes(enc(canonicalizeJcs(v))))}
async function tagged(tag:number,data:Uint8Array){const b=new Uint8Array(data.length+1);b[0]=tag;b.set(data,1);return sha256Bytes(b)}
export async function merkleRoot(values:unknown[]){if(!values.length)return hex(await sha256Bytes(new Uint8Array()));let level=await Promise.all(values.map(v=>tagged(0,enc(canonicalizeJcs(v)))));while(level.length>1){if(level.length%2)level.push(level[level.length-1]);const next:Bytes[]=[];for(let i=0;i<level.length;i+=2){const b=new Uint8Array(1+level[i].length+level[i+1].length);b[0]=1;b.set(level[i],1);b.set(level[i+1],1+level[i].length);next.push(await sha256Bytes(b))}level=next}return hex(level[0])}
export async function buildRunManifest(run_id:string,events:unknown[],effects:unknown[],metadata:Record<string,unknown>={}){return {manifest_version:"agent-ledger-run-manifest/1",canonicalization:"RFC8785",hash:"SHA-256",run_id,event_count:events.length,event_root:await merkleRoot(events),effect_count:effects.length,effect_root:await merkleRoot(effects),metadata}}
export async function compareReplay(expected:unknown[],actual:unknown[]){const divergences:any[]=[];let matched=0;for(let i=0;i<Math.max(expected.length,actual.length);i++){if(i>=expected.length)divergences.push({index:i,kind:"unexpected",expected:null,actual:actual[i]});else if(i>=actual.length)divergences.push({index:i,kind:"missing",expected:expected[i],actual:null});else if(await sha256Jcs(expected[i])!==await sha256Jcs(actual[i]))divergences.push({index:i,kind:"content",expected:expected[i],actual:actual[i]});else matched++}return{matched,equivalent:divergences.length===0,effects_executed:false,divergences}}

// --- Adapter contracts: storage/blob/framework seams ---
export interface StateStore { get(namespace:string,key:string):Promise<Record<string,unknown>|null>; put(namespace:string,key:string,value:Record<string,unknown>,expectedRevision?:number):Promise<number>; delete(namespace:string,key:string):Promise<void> }
export class MemoryStateStore implements StateStore { private rows=new Map<string,{value:Record<string,unknown>,revision:number}>(); private k(n:string,k:string){return `${n}\0${k}`} async get(n:string,k:string){const r=this.rows.get(this.k(n,k));return r?{...structuredClone(r.value),_revision:r.revision}:null} async put(n:string,k:string,v:Record<string,unknown>,expectedRevision?:number){const key=this.k(n,k),r=this.rows.get(key),rev=r?.revision??0;if(expectedRevision!==undefined&&expectedRevision!==rev)throw new Error(`stale revision: expected ${expectedRevision}, found ${rev}`);this.rows.set(key,{value:structuredClone(v),revision:rev+1});return rev+1} async delete(n:string,k:string){this.rows.delete(this.k(n,k))} }
export interface BlobStore { put(data:Uint8Array):Promise<string>; get(ref:string):Promise<Uint8Array> }
export interface RuntimeAdapter { framework:string; runStore:DurableRunStore; effectLedger:EffectLedger }
export function frameworkAdapter(framework:string,runStore:DurableRunStore,effectLedger:EffectLedger):RuntimeAdapter{return{framework,runStore,effectLedger}}
export const adapters={langgraph:frameworkAdapter.bind(null,"langgraph"),langchain:frameworkAdapter.bind(null,"langchain"),crewai:frameworkAdapter.bind(null,"crewai"),autogen:frameworkAdapter.bind(null,"autogen"),openaiAgents:frameworkAdapter.bind(null,"openai-agents"),llamaindex:frameworkAdapter.bind(null,"llamaindex"),semanticKernel:frameworkAdapter.bind(null,"semantic-kernel")};
export function validEffectTransition(from:EffectStatus,to:EffectStatus){return transitions[from].includes(to)}
