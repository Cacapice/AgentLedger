# v4.5.0 Developer Adoption Release
Adds hosted action receipts and verification, Python action decorator, OpenAI Agents tracing processor, OpenTelemetry bridge, policy primitive, TypeScript `action()`/`receipt()`, MCP receipt/policy tools, five-minute CLI init/doctor/verify flow, six copyable examples, and developer-distribution/accountability documentation.

## Production boundaries
OpenAI integration is an optional processor and must be registered with the Agents SDK by the application. The OpenTelemetry bridge maps normalized span dictionaries; it is not yet a full OTLP collector. MCP is an instrumentation/control server, not yet a transparent OAuth reverse proxy. Policy enforcement is a deterministic SDK primitive; approval workflow orchestration remains future work. `VERIFIED` does not mean compliance certification or external anchoring unless independently configured and checked.
