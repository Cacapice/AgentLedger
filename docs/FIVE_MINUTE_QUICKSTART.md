# Five-minute quickstart: one real agent action, one verifiable receipt

This is the canonical Agent Ledger demonstration. It dogfoods Agent Ledger with a real, read-only Scuderia agent action against the public Scuderia Lifestyle site.

## 0. What the demo proves

The agent performs a live HTTP indexability observation of `https://www.scuderialifestyle.org/maxima/`, records who/what/authority/policy/result, sends the event to your deployed Agent Ledger Worker, receives an opaque `alr_...` receipt, and immediately retrieves that receipt through the verification API.

It does **not** mutate Scuderia, Search Console, sitemaps, content, or external accounts.

## 1. Install the SDK from this release

From the `agent-ledger` repository root:

```bash
python -m pip install -e packages/python
```

After the public PyPI package is published, the equivalent is:

```bash
pip install agent-ledger
```

## 2. Configure your deployed Worker

Use a tenant API key with at least `events:write`, `usage:read`, and `audit:read`.

```bash
agent-ledger init --url https://YOUR-WORKER.workers.dev --api-key al_YOUR_KEY
agent-ledger doctor
```

`agent-ledger` automatically loads `.env.agent-ledger` for its CLI commands. Do not commit this file.

## 3. Run the real Scuderia agent

```bash
agent-ledger dogfood-scuderia
```

Expected shape:

```text
✓ Scuderia live observation: https://www.scuderialifestyle.org/maxima/
✓ HTTP 200 · canonical=yes · noindex=no
✓ Hosted receipt: alr_<opaque receipt id>
✓ Receipt alr_<opaque receipt id> VERIFIED
✓ Agent: scuderia-indexability-agent
✓ Action: seo.indexability.observe
✓ Policy attribution
✓ Event hash
✓ Chain link

Canonical proof command:
agent-ledger verify alr_<opaque receipt id>
```

The exact HTTP/canonical result reflects the live page at run time.

## 4. Verify it independently from the CLI

Copy the returned receipt ID:

```bash
agent-ledger verify alr_<receipt-id>
```

For machine-readable evidence:

```bash
agent-ledger verify alr_<receipt-id> --json
```

## 5. What was recorded

- **Agent:** `scuderia-indexability-agent@1.0.0`
- **Action:** `seo.indexability.observe`
- **Tool:** `http.fetch`
- **Authority:** `scuderia-operator`
- **Policy:** `scuderia-public-observation-v1@1`
- **Decision:** `ALLOWED`
- **Resource:** Scuderia-owned web page
- **Result:** live HTTP/indexability observation
- **Evidence:** local source-chain event + hosted tenant-chain receipt

## Integrity boundary

`VERIFIED` means the hosted event exists and the receipt's event/agent/chain evidence checks pass under the current Agent Ledger verification model. It does not by itself mean an independent external anchor exists, that D1 is WORM storage, or that any regulatory certification has been achieved. Configure external signing/anchoring for higher-assurance deployment evidence.
