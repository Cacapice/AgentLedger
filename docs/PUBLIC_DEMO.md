# Public demonstration: Scuderia → Agent Ledger

## The 30-second story

A Scuderia autonomous SEO agent performs a real read-only observation of a Scuderia-owned web page. Agent Ledger records the agent identity, action, authority, policy, result, and hash-chain evidence, then returns an opaque receipt that can be verified from the CLI.

```text
Scuderia public page
        │
        ▼
scuderia-indexability-agent
        │  http.fetch / seo.indexability.observe
        ▼
Agent Ledger ingestion
        │
        ├── source provenance
        ├── tenant chain
        ├── policy attribution
        └── receipt: alr_...
        │
        ▼
agent-ledger verify alr_...
```

## Live command

```bash
agent-ledger dogfood-scuderia
```

## Proof command

```bash
agent-ledger verify alr_<receipt-id>
```

Do not publish a placeholder receipt as if it were production evidence. Replace `<receipt-id>` only with a receipt returned by an actual deployed Worker run. A public screenshot or recording should show the receipt ID, verification result, agent/action/policy fields, and no API key.

## Suggested public caption

> A Scuderia SEO agent just performed a live read-only indexability observation. Agent Ledger recorded who acted, what it did, under which policy and authority, and returned a tamper-evident receipt. The same receipt can be verified from the CLI.

Agent Ledger supports accountability and audit evidence; it is not itself a compliance certification.
