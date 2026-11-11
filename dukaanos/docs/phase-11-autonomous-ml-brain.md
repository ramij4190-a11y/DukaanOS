# Phase 11: The Autonomous Self-Learning Kirana Brain
### Continuous Online Learning, Auto-Adaptive Demand Intelligence & Self-Driving Store Operations

---

## 1. Executive Problem & Objective

Traditional retail ERPs are passive databases: they wait for a human to manually type numbers, run reports, and manually figure out what to do. If a storekeeper doesn't manually audit stock or place orders, the software stays silent while the business bleeds cash from stockouts and dead capital.

**Phase 11 transforms DukaanOS into an active, self-learning retail brain.**
When the storekeeper speaks into the voice interface or sells items at the counter, the system does not just record transactions—**it continuously learns the unique physics of that specific retail store** and operates autonomously:

1. **Continual Online Learning (No Batch Delay):**
   - Updates demand velocity $\mu_{d}$ and standard deviation $\sigma_{d}$ incrementally with every sale and voice event using Exponentially Weighted Moving Statistics (EWMA).
   - Learns supplier lead-time realities (e.g., ITC arrives in 1.8 days; local oil supplier takes 3.5 days).
   - Adapts to hyper-local day-of-week and festive cycles automatically.

2. **Autonomous Self-Driving Operations (Auto-Pilot Mode):**
   - **Autonomous Reorder Trigger:** When projected stock crosses the dynamically updated Reorder Point ($\text{ROP}_t$), the brain automatically drafts a consolidated PO and pre-stages WhatsApp supplier dispatches.
   - **Autonomous Shrinkage & Spoilage Shield:** Detects stagnant, slow-moving perishable batches and automatically triggers bundling/discount suggestions before expiry write-offs occur.
   - **Autonomous Khata Vigilance:** Dynamically throttles credit limits for customers who miss typical repayment windows.
   - **Autonomous Voice Morning Brief:** Pre-computes the store's daily tactical plan and speaks it aloud in vernacular Hindi/Hinglish upon store opening.

---

## 2. Mathematical Formulations for Continual Online Learning

Instead of heavy periodic batch retraining, DukaanOS deploys **Welford's Algorithm & EWMA** for ₹0 low-compute, real-time incremental learning on modest store hardware:

### A. Online Velocity & Volatility Learning
For each product SKU $i$ upon arrival of transaction at step $k$:
$$\mu_{k} = (1 - \alpha) \mu_{k-1} + \alpha d_k$$
$$\sigma^2_{k} = (1 - \beta) \sigma^2_{k-1} + \beta (d_k - \mu_k)^2$$

Where:
- $\alpha \in [0.1, 0.2]$: Decay rate for demand velocity (adapts quickly to trends).
- $\beta \in [0.05, 0.1]$: Volatility sensitivity factor.

### B. Dynamically Auto-Tuned Reorder Point (ROP)
$$\text{ROP}_t = \left(\mu_{k} \times \hat{L}_s\right) + Z \times \sqrt{\hat{L}_s \times \sigma^2_k + \mu^2_k \times \sigma^2_{L, s}}$$

Where:
- $\hat{L}_s$: Auto-learned lead time of supplier $s$.
- $\sigma^2_{L, s}$: Supplier delivery variance.
- $Z = 1.65$ (95% non-stockout service level).

### C. Run-Out Horizon (Depletion Countdown)
$$\text{DaysToDepletion}_t = \frac{\text{CurrentStock}_t}{\max(\mu_k, 0.1)}$$
If $\text{DaysToDepletion}_t \le \hat{L}_s + 1$, the Autonomous Brain automatically generates a **CRITICAL RESTOCK ACTION**.

---

## 3. Autonomous Operational Event Loop

```
  [Voice Inward / Damage / POS Sale]
                 │
                 ▼
  ┌───────────────────────────────────────────────┐
  │     Event-Sourced Immutable Ledger Update      │
  │     (Atomic Balance: CurrentStock_t)          │
  └──────────────────────┬────────────────────────┘
                         │
                         ▼
  ┌───────────────────────────────────────────────┐
  │       Autonomous ML Learning Hook             │
  │  1. Updates Online Demand Velocity (EWMA)     │
  │  2. Recomputes SKU Volatility & Depletion Day │
  │  3. Refreshes Statistical Safety Buffers      │
  └──────────────────────┬────────────────────────┘
                         │
                         ▼
  ┌───────────────────────────────────────────────┐
  │        Self-Driving Rule Inference            │
  │  • If DaysToDepletion <= LeadTime + 1:        │
  │      ➔ Auto-Draft Purchase Order              │
  │  • If Stock > 3x ROP & Velocity Decaying:     │
  │      ➔ Auto-Flag Dead Capital Promo           │
  │  • If Voice Damage Spike Detected:            │
  │      ➔ Flag Vendor Quality Warning            │
  └──────────────────────┬────────────────────────┘
                         │
                         ▼
  ┌───────────────────────────────────────────────┐
  │         Proactive Voice & Web UI Feed         │
  │  "Ramesh Ji, Atta stock agle 2 din me khatam  │
  │   hoga. Maine ITC ke liye 35 bags ka PO auto- │
  │   prepare kar diya hai!"                      │
  └───────────────────────────────────────────────┘
```

---

## 4. Key Metrics & Business Impact

| Capability | Static Legacy ERP | DukaanOS Autonomous Brain |
| :--- | :--- | :--- |
| **Model Retraining** | Monthly manual batch | **Instant online update on every voice / sale event** |
| **Reorder Decision** | Shopkeeper writes on paper at night | **Autonomous calculation based on learned burn-rate** |
| **Stockout Warning** | After shelves are already empty | **48-72 hours predictive lead time buffer** |
| **Interaction Mode** | Typing in 15 different desktop forms | **Natural voice interaction + auto-pilot execution** |
| **Compute Cost** | Expensive GPU cloud servers | **₹0 local Python incremental math (runs on any PC)** |
