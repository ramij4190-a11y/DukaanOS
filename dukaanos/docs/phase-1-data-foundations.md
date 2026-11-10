# Phase 1: Python & Data Engineering Foundations

## 1. Overview & Objectives
- **Target Role:** Data Engineer / Retail Intelligence Analyst
- **Goal:** Build a robust, reproducible retail data pipeline capable of simulating, ingesting, cleaning, and auditing real-world Indian grocery (Kirana) operations.
- **Timeframe:** Month 1

---

## 2. Business Context: The Indian Kirana Operating Environment
Small retail in India has unique operational characteristics that standard Western e-commerce datasets do not capture:
1. **High SKU Count, Tight Margins:** Staples operate at 6–10% gross margin, while packaged snacks and personal care operate at 15–28%.
2. **Micro-Baskets & Cash Flow:** Frequent, low-value transactions (average basket size ₹140–₹200).
3. **Multi-Channel Payments:** High penetration of UPI (~50%), heavy cash dependence (~40%), and trust-based local credit (*Khata*, ~10%).
4. **Demand Drivers:** Weekly weekend cycles (+35%), month-beginning salary cycles (1st to 7th, +25%), and pronounced festival spikes (Diwali, Dhanteras, Holi, Eid).
5. **Operational Fragility:** High risk of silent stockouts and damaged/expired goods (shrinkage).

---

## 3. System Architecture & Components

```
dukaanos/data/raw/
   ├── products.csv          (100 SKUs, 5 categories, margins, lead times, safety stocks)
   ├── suppliers.csv         (4 verified FMCG & Mandi suppliers)
   ├── sales_raw.csv         (279,266 raw transactions with duplicates & missing fields)
   ├── inventory_ledger.csv  (40,930 traceable stock events)
   └── purchase_orders.csv   (4,604 supplier purchase orders)
          │
          ▼
dukaanos/src/dukaanos/data_pipeline/cleaner.py
   ├── Deduplication         (Identifies and removes duplicate sales records)
   ├── Imputation            (Cleans and imputes missing payment methods)
   └── Stockout Isolation    (Separates fulfilled sales from unfulfilled demand)
          │
          ▼
dukaanos/data/processed/
   ├── sales_clean.csv       (274,701 clean fulfilled transactions)
   ├── stockouts.csv         (438 logged stockout signals, 1,816 unfulfilled units)
   └── ledger_clean.csv      (Chronologically ordered, verified inventory balance)
          │
          ▼
dukaanos/src/dukaanos/data_pipeline/metrics.py
   ├── Executive Scorecard   (Annual revenue, COGS, gross profit, margin %)
   ├── Category Breakdown    (Volume and profitability across all 5 retail categories)
   ├── Assortment Rank       (Top 10 revenue drivers vs. Bottom 10 slow movers)
   └── Ledger Reconciliation (100% mathematical conservation audit)
          │
          ▼
dukaanos/src/dukaanos/analysis/visualizer.py
   └── reports/charts/       (5 high-resolution publication charts)
```

---

## 4. Key Engineering Decisions & Mathematics

### A. The Immutable Inventory Ledger
In naive systems, stock is updated by overwriting a number:
$$\text{stock} = \text{new\_value}$$
This destroys history. In DukaanOS, stock is an event-sourced ledger:
$$\text{Stock}(t) = \text{Stock}(0) + \sum_{i=1}^t \Delta q_i$$
Where $\Delta q_i$ is positive for purchases and negative for sales and shrinkage.
**Audit Result:** 100 out of 100 SKUs achieved 100% mathematical conservation with 0 discrepancies.

### B. Censored Demand vs. Pure Sales
Standard sales data only records fulfilled transactions:
$$S_t = \min(D_t, I_t)$$
Where $D_t$ is true customer demand and $I_t$ is available inventory. When $I_t = 0$, $S_t = 0$.
If an ML model trains on $S_t$ directly, it learns that customer demand was zero, leading to perpetual under-ordering. DukaanOS explicitly partitions unfulfilled demand signals ($D_t - S_t > 0$) into `stockouts.csv`.

---

## 5. Acceptance Criteria Checklist
- [x] 100 realistic SKUs across 5 retail categories.
- [x] 365 days of chronological sales, ledger, and purchase orders.
- [x] Automated ETL cleaning script that logs duplicates and missing data.
- [x] Business metrics calculator (Revenue, COGS, Profit, Margin, Payment mix).
- [x] Publication-grade Matplotlib/Seaborn visual charts.
- [x] 100% passing automated test suite (`pytest tests/test_pipeline.py`).
- [x] Architectural documentation and Git history.

