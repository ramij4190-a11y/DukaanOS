# Phase 4: LLM Engineering & Autonomous Business Agents

## 1. Executive Summary & Goals
- **Role Transition:** From Backend Engineer to Applied AI & Forward Deployed Engineer (FDE)
- **Core Mission:** Construct an agentic retail operations assistant that can understand natural language requests (in English, Hindi, and Hinglish), fetch ground-truth database intelligence via deterministic tools, and propose human-in-the-loop business actions.
- **Timeframe:** Month 4
- **Tech Stack:** Function calling, Structured Outputs (Pydantic), Tool Orchestration, pgvector (Semantic search for catalog & invoices), Guardrails.

---

## 2. Agent Architecture & Tool Execution Flow

```
Shopkeeper Voice / Text: "Agami kal kon kon product order korte hobe?" / "Kal ke liye kya order karna hai?"
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │   LLM Intent & Entity Extraction     │
            └──────────────────┬───────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │       Approved Tool Calling          │
            │  - get_inventory_status()            │
            │  - get_demand_forecast()             │
            │  - calculate_reorder_quantities()    │
            └──────────────────┬───────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │    Business Validation & Policy      │
            │  - Supplier min-order value checks   │
            │  - Cash flow budget limits           │
            └──────────────────┬───────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │       Proposed Action Draft          │
            │  "Suggested Purchase Order: ₹14,200" │
            └──────────────────┬───────────────────┘
                               │
                 Human Confirmation Required?
                               ├────────────────┐
                          [Yes]                 [No / Edit]
                               ▼                        ▼
                ┌─────────────────────┐    ┌─────────────────────┐
                │ Execute Transaction │    │ Revise & Re-prompt  │
                │ & Append to Ledger  │    └─────────────────────┘
                └─────────────────────┘
```

---

## 3. Strict Safety Principles (The FDE Mindset)

1. **The LLM Never Writes Directly to the Database:** The LLM can only query read-only tools or generate a structured proposal payload (`DraftPurchaseOrder`).
2. **Explicit Human-in-the-Loop Approval:** Financial and inventory transactions always require physical retailer confirmation (`Confirm Order` button or PIN).
3. **Audit Logging:** Every prompt, tool invocation, returned tool state, and executed action is logged with latency, token usage, and tenant ID.
