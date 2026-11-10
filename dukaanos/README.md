# DukaanOS (दुकानOS)
### AI-Powered Retail Operating System for Indian Small Retailers & Kirana Stores

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 1. Executive Vision
Small independent retailers (Kirana stores, general provision shops) power the backbone of India's retail economy. However, over 90% of them operate with manual intuition or primitive billing registers. They suffer from:
1. **Unseen Stockouts:** Losing high-margin customer baskets due to silent stock depletion.
2. **Dead Capital:** Overstocking slow-moving SKUs that trap operating cash flow.
3. **Censored Demand:** Confusing zero sales with zero demand (when in reality, inventory was depleted).
4. **Tedious Reordering:** Spending hours every evening guessing what to purchase from various distributors.

**DukaanOS** is an intelligent operating system designed to give small retail owners predictive demand intelligence, automated purchase planning, inventory optimization, and an interactive business operations agent.

---

## 2. Technical Architecture Overview

DukaanOS is engineered across six cohesive layers:

```
[Layer 1: Ingestion]      --> Manual Entry, Invoices (OCR), CSVs, Barcodes
[Layer 2: Data Eng.]      --> PostgreSQL Ledger, Traceable Stock Delta, Alembic, Redis
[Layer 3: ML Engine]      --> Demand Forecasting (LightGBM/Prophet), Anomaly Detection, Assortment
[Layer 4: Agent & LLM]    --> Tool-Calling Business Assistant (Reorder, Khata, Inquiries)
[Layer 5: App Layer]      --> Next.js / React Retailer Dashboard & Fast API Gateway
[Layer 6: Observability]  --> MLflow, Prediction Bias Tracking, Tenant Isolation, Audit Logs
```

---

## 3. Project 001: Retail Intelligence Dataset & Analytics Engine

The foundation of DukaanOS begins with clean, auditable operational data. **Project 001** builds a production-grade synthetic simulation of an Indian Kirana business operating over 365 days.

### Specifications
- **Catalog Size:** 100 realistic SKUs across 5 core retail categories:
  - `Staples & Grains` (Atta, Basmati Rice, Toor Dal, Sugar, Spices)
  - `Edible Oils & Ghee` (Mustard Oil, Sunflower Oil, Desi Ghee tins & pouches)
  - `Packaged Foods & Snacks` (Maggi, Parle-G, Chips, Biscuits, Tea, Coffee)
  - `Personal & Home Care` (Detergents, Soaps, Toothpastes, Cleaners, Shampoos)
  - `Dairy & Fresh Essentials` (Milk pouches, Curd, Bread, Butter, Eggs)
- **Time Horizon:** 365 consecutive operational days (2025-01-01 to 2025-12-31).
- **Market Dynamics Simulated:**
  - **Weekly Footfall Cycles:** Saturday/Sunday spikes (+35%).
  - **Salary Week Surge:** 1st to 7th of every month (+25% staple and grocery restocking).
  - **Festivals:** Diwali / Dhanteras surge, Holi, and Eid surges.
  - **Payment Mix:** UPI (~49.5%), Cash (~40.6%), and Khata Credit (~9.9%).
  - **Shrinkage & Damage:** Real-world pack damages and shelf expiry write-offs.
  - **Censored Demand:** Zero sales flagged as stockouts when inventory is exhausted.

---

## 4. Key Engineering Decisions

### Decision 1: The Immutable Inventory Ledger
In traditional naive retail software, stock is stored as a single numeric column (`current_quantity = 50`) that gets overwritten. If a count error occurs, it is impossible to reconstruct history.

DukaanOS implements an **event-sourced inventory ledger**:
$$\text{Stock}_t = \text{OpeningStock} + \sum \text{Purchases} - \sum \text{Sales} - \sum \text{Damages}$$

Every single movement requires:
- `transaction_id`
- `event_type` (`OPENING_STOCK`, `PURCHASE`, `SALE`, `DAMAGE_EXPIRED`)
- `quantity_change`
- `running_balance`
- `reference_id` (Invoice # or Purchase Order #)

**Result:** In our audit of 100 SKUs and 40,930 ledger events, the mathematical integrity score is **100.0% with zero discrepancies**.

### Decision 2: Handling Real-World Data Imperfections
Real Kirana data is dirty. Project 001 implements:
- Automated deduplication of sales records (4,127 duplicate entries identified and removed).
- Robust imputation of missing payment methods.
- Separation of fulfilled sales vs unfulfilled stockouts (preserving pure demand signals for ML).

---

## 5. Annual Business Intelligence Scorecard (2025)

| Metric | Result | Indian Retail Insight |
| :--- | :--- | :--- |
| **Total Store Revenue** | **₹3.89 Crore** (₹38,872,063) | Typical annual turnover of an active neighborhood Kirana |
| **Cost of Goods Sold (COGS)** | **₹3.37 Crore** | High inventory turnover |
| **Gross Profit** | **₹52.08 Lakh** | Real operating gross profit before shop overheads |
| **Overall Gross Margin** | **13.4%** | Realistic blend across low-margin staples and high-margin care items |
| **Average Daily Revenue** | **₹106,498** | Consistent baseline with weekend jumps |
| **Average Basket Value** | **₹141.51** | Micro-transactions typical of Indian retail |
| **Payment Breakdown** | UPI: 49.5%, Cash: 40.6%, Khata: 9.9% | Strong digital payment adoption with local credit trust |
| **Estimated Stockout Loss** | **₹4.33 Lakh** (1,816 units lost) | **Immediate revenue opportunity for DukaanOS ML forecasting!** |

### Category Breakdown
```
Category                     | Revenue        | Margin % | Units Sold
----------------------------------------------------------------------
Edible Oils & Ghee           | ₹98.12 Lakh    |   10.2%  |     42,287
Personal & Home Care         | ₹85.13 Lakh    |   18.3%  |     93,156
Packaged Foods & Snacks      | ₹82.80 Lakh    |   15.6%  |    124,846
Staples & Grains             | ₹71.33 Lakh    |   10.7%  |     70,913
Dairy & Fresh Essentials     | ₹51.34 Lakh    |   11.6%  |     99,571
```

---

## 6. Visual Analytics Artifacts

High-resolution charts generated in `reports/charts/`:
1. `daily_sales_trend.png` — 365-day store revenue trajectory with 7-day and 30-day moving averages and festival peaks.
2. `category_performance.png` — Revenue contribution vs. gross margin percentage per category.
3. `top_vs_slow_products.png` — Top 10 revenue powerhouses vs. bottom 10 slow-movers (dead capital risk).
4. `payment_methods.png` — Distribution of UPI, Cash, and Khata credit volume.
5. `inventory_ledger_trace.png` — Complete running stock trace for representative SKU (e.g. Aashirvaad Atta 5kg).

---

## 7. How to Run & Verify

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12 on Windows)
- Virtual environment (`.venv`)

### 2. Quickstart Execution
```bash
# Run complete pipeline (ETL + KPIs + Charts generation)
python dukaanos/run_project_001.py

# Run automated test suite
python -m pytest dukaanos/tests -v
```

---

## 8. Phase Progress & Engineering Milestones

### Completed Milestones:
- [x] **Phase 1: Retail Data Foundations & Project 001**
  - Blueprint: [`docs/phase-1-data-foundations.md`](file:///d:/Ai/dukaanos/docs/phase-1-data-foundations.md)
  - 100 SKUs, 5 categories, 365-day realistic Indian Kirana simulation.
  - Automated ETL data cleaner with deduplication, null imputation, and stockout isolation.
  - Event-sourced immutable inventory ledger (100% mathematical conservation across 40,930 events).
  - Business intelligence executive scorecard (₹3.90 Cr turnover, ₹52.20 Lakh gross profit, 13.4% margin).

- [x] **Phase 2: Machine Learning & Retail Intelligence Engine**
  - Blueprint: [`docs/phase-2-machine-learning-engine.md`](file:///d:/Ai/dukaanos/docs/phase-2-machine-learning-engine.md)
  - Time-series rolling-origin cross-validation (walk-forward backtesting across 3 holdout folds).
  - Feature engineering (lags, rolling statistics, calendar cycles, salary weeks, festivals) with zero lookahead bias.
  - Forecasting benchmark: LightGBM achieved top performance (26.07% WAPE vs 28.49% Naive Moving Average).
  - Statistical Z-score and Isolation Forest anomaly detection (523 velocity spikes/drops detected).
  - Market basket association analysis (1,687 cross-selling affinity pairs, including Maggi + Ketchup with 7.53x Lift).
  - Statistical dynamic reorder point (ROP) and safety stock engine generating prioritized purchase orders.

- [x] **Phase 3: Backend & Data Engineering**
  - Blueprint: [`docs/phase-3-backend-and-data-engineering.md`](file:///d:/Ai/dukaanos/docs/phase-3-backend-and-data-engineering.md)
  - Production FastAPI REST service with multi-tenant SQLAlchemy 2.0 schema (`Store`, `User`, `Product`, `InventoryLedger`, `SalesTransaction`, `PurchaseOrder`).
  - Strict tenant isolation enforced at the JWT dependency layer.
  - Idempotency protection (`Idempotency-Key` header) guaranteeing zero double-deductions or duplicate billing.
  - Atomic inventory ledger mutations and stock reconciliation endpoints.
  - Morning store briefing endpoint (`/api/v1/intelligence/daily-brief`).

- [x] **Phase 4: LLM Engineering & Autonomous Business Agents**
  - Blueprint: [`docs/phase-4-llm-and-ai-agents.md`](file:///d:/Ai/dukaanos/docs/phase-4-llm-and-ai-agents.md)
  - Forward Deployed Engineer (FDE) agent workflow supporting multi-lingual queries (English, Hindi, Hinglish, Bengali).
  - Deterministic tool orchestration (`get_inventory_status`, `get_low_stock_products`, `get_product_forecast`, `calculate_reorder_quantities`, `draft_purchase_order_proposal`).
  - Zero hallucination guarantee: agent never invents quantities or writes directly to the database.
  - Safety guardrails (budget caps, quantity ceilings, human approval gates).
  - Two-phase execution: agent prepares structured draft proposals, executing only upon explicit shopkeeper confirmation.

- [x] **Phase 5: Production ML Systems, MLOps & Observability**
  - Blueprint: [`docs/phase-5-production-mlops.md`](file:///d:/Ai/dukaanos/docs/phase-5-production-mlops.md)
  - Versioned model registry with artifact serialization, metadata tracking, and stage transitions (`PRODUCTION` / `ARCHIVED`).
  - Real-time Population Stability Index (PSI) & Kolmogorov-Smirnov (KS-test) data drift monitoring.
  - Automated model degradation detection (spikes in 14-day WAPE trigger `TRIGGER_AUTOMATED_RETRAINING`).
  - Production structured JSON logging for Grafana/CloudWatch and operational telemetry metrics.
  - Multi-stage non-root `Dockerfile`, `docker-compose.yml` (PostgreSQL + Redis + FastAPI), and GitHub Actions CI/CD workflow.

### Upcoming Architecture Blueprints:
- [ ] **Phase 6:** [`docs/phase-6-field-deployment-and-startup.md`](file:///d:/Ai/dukaanos/docs/phase-6-field-deployment-and-startup.md) — Storekeeper pilot onboarding, ROI measurement, willingness-to-pay validation.

