# Engineering Decisions Log — DukaanOS

### ADR 001: Event-Sourced Inventory Ledger vs. Mutable Stock Counter
- **Context:** Most retail software stores stock as a mutable numeric column (`stock_quantity`) on the `products` table.
- **Problem:** When physical audits show discrepancy with digital records, or when concurrent sales/deliveries occur, there is zero traceability into why stock drifted.
- **Decision:** Implement an immutable ledger where every inventory change is an atomic append-only event (`OPENING_STOCK`, `PURCHASE`, `SALE`, `DAMAGE_EXPIRED`, `RETURN`).
- **Consequence:** 
  - Allows full point-in-time reconstruction of inventory state on any historical date.
  - Guarantees 100% auditability and mathematical conservation ($\text{Balance} = \text{Opening} + \text{In} - \text{Out}$).
  - Slightly higher storage requirement, trivially mitigated by indexing on `(product_id, date)`.

### ADR 002: Separating Unfulfilled Stockout Signals from Pure Sales
- **Context:** In standard POS systems, when a product goes out of stock, zero sales are recorded.
- **Problem (Censored Demand):** Naive ML models trained on sales history will falsely learn that consumer demand dropped to zero on stockout days, rather than recognizing stock unavailability.
- **Decision:** Explicitly capture unfulfilled stockout signals during data processing, separating pure sales from lost demand.
- **Consequence:** Future demand forecasting models in Phase 2 can use demand imputation or censored regression instead of treating zero sales as zero demand.

### ADR 003: Categorical Granularity & Pricing Realism
- **Context:** FMCG margins in India vary drastically by product category.
- **Decision:** Model realistic margins:
  - Staples & Grains: 6% – 10%
  - Edible Oils & Ghee: 7% – 12%
  - Dairy & Fresh: 8% – 15%
  - Packaged Snacks & Foods: 14% – 22%
  - Personal & Home Care: 18% – 28%
- **Consequence:** Retail metrics and recommendations reflect the actual economic pressures and cash-flow trade-offs of Indian shopkeepers.

