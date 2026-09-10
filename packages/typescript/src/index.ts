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
