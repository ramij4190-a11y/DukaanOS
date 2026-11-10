# Phase 2: Machine Learning & Retail Intelligence Engine

## 1. Executive Summary & Goals
- **Role Transition:** From Data Engineer to Applied AI/ML Engineer
- **Core Mission:** Design, train, evaluate, and benchmark production-grade machine learning models to solve real grocery inventory challenges without relying on black-box external LLM APIs.
- **Timeframe:** Month 2
- **Core Principle:** Never jump straight to deep learning or LLMs when robust classical ML and statistical baselines deliver higher interpretability, lower compute costs, and superior performance on small tabular retail datasets.

---

## 2. The Four ML Systems to Build

```
                      ┌────────────────────────────────────────┐
                      │   DukaanOS Machine Learning Engine     │
                      └──────────────────┬─────────────────────┘
                                         │
         ┌───────────────────┬───────────┴───────────┬───────────────────┐
         ▼                   ▼                       ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   A. Demand     │ │   B. Anomaly    │ │  C. Assortment  │ │ D. Inventory    │
│   Forecasting   │ │    Detection    │ │ & Association   │ │  Optimization   │
│                 │ │                 │ │                 │ │                 │
│ 7 & 14-day SKU  │ │ Sudden surges,  │ │ Frequent basket │ │ Safety stock,   │
│ demand estimates│ │ zero-velocity,  │ │ pairs, cross-   │ │ ROP, lead-time  │
│ via LightGBM    │ │ stock shrinkage │ │ sell rules      │ │ purchase orders │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 3. Mathematical Formulations & Evaluation Metrics

### A. Time-Series Train/Test Split (Never Random Shuffle!)
Standard cross-validation randomly shuffles data rows, leaking future knowledge into the past (*lookahead bias*).
In DukaanOS, we enforce **Rolling-Origin Backtesting (Walk-Forward Validation)**:

```
Fold 1: [--- Train: Jan-Aug ---] [ Test: Sep (14 days) ]
Fold 2: [------ Train: Jan-Sep ------] [ Test: Oct (14 days) ]
Fold 3: [--------- Train: Jan-Oct ---------] [ Test: Nov (14 days) ]
```

### B. Evaluation Metrics: Why WAPE Beats MAPE
In retail, daily sales for individual SKUs frequently include zeros or small integers (1 or 2 units).
- **MAPE (Mean Absolute Percentage Error)**:
  $$\text{MAPE} = \frac{1}{N} \sum_{t=1}^N \left| \frac{y_t - \hat{y}_t}{y_t} \right|$$
  *Failure Mode:* When $y_t = 0$, MAPE divides by zero. When $y_t = 1$ and prediction is $2$, error is $100\%$, unfairly penalizing low-velocity items.
- **WAPE (Weighted Absolute Percentage Error)**:
  $$\text{WAPE} = \frac{\sum_{t=1}^N |y_t - \hat{y}_t|}{\sum_{t=1}^N y_t}$$
  *Advantage:* Scales total absolute error by total actual volume. Zero-safe and volume-weighted.
- **MAE (Mean Absolute Error):**
  $$\text{MAE} = \frac{1}{N} \sum_{t=1}^N |y_t - \hat{y}_t|$$
- **Forecast Bias (Tracking Signal):**
  $$\text{Bias} = \frac{\sum_{t=1}^N (\hat{y}_t - y_t)}{\sum_{t=1}^N y_t}$$
  *Insight:* Positive bias indicates systematic over-forecasting (excess inventory/holding costs); negative bias indicates systematic under-forecasting (risk of stockouts).

### C. Inventory Optimization Mathematics
1. **Lead-Time Demand ($\mu_{L}$):**
   $$\mu_L = \bar{d} \times L$$
   Where $\bar{d}$ is forecasted average daily demand and $L$ is supplier lead time in days.
2. **Safety Stock ($SS$):**
   $$SS = Z_\alpha \times \sqrt{L \cdot \sigma_d^2 + \bar{d}^2 \cdot \sigma_L^2}$$
   Where $Z_\alpha$ is the standard normal z-score for desired service level (e.g. $Z_{95\%} = 1.645$), $\sigma_d$ is standard deviation of demand, and $\sigma_L$ is lead-time variance.
3. **Reorder Point (ROP):**
   $$\text{ROP} = \mu_L + SS$$
   When $\text{Current Stock} + \text{Pending Orders} \le \text{ROP}$, generate a purchase recommendation.

---

## 4. Feature Engineering Architecture

Raw sales dates and quantities are transformed into predictive tabular features:

| Feature Group | Features | Business Justification |
| :--- | :--- | :--- |
| **Calendar & Cycles** | `day_of_week`, `day_of_month`, `is_weekend`, `is_salary_week` | Captures weekend surges and 1st–7th monthly grocery restocking |
| **Festival Proximity** | `is_festival`, `days_to_festival` | Anticipates pre-Diwali, Holi, and Eid surges |
| **Lags (Autoregressive)** | `lag_1`, `lag_7`, `lag_14`, `lag_21` | Same-day-last-week velocity is the strongest short-term predictor |
| **Rolling Statistics** | `rolling_mean_7`, `rolling_std_7`, `rolling_mean_30` | Smooths noise and captures recent velocity shifts |
| **Category Context** | `category_daily_mean_volume` | Informs product predictions based on broader category momentum |

---

## 5. Solving The Hard Technical Challenges

### Challenge 01: Cold-Start Problem (New SKUs / Stores)
When a store introduces a new SKU (0 sales history), autoregressive lags (`lag_7`) do not exist.
**DukaanOS Cold-Start Fallback Strategy:**
$$\hat{y}_{\text{new\_sku}} = \text{Category Median Daily Velocity} \times \text{Price Tier Ratio} \times \text{Day-of-Week Multiplier}$$
As sales accumulate:
- Days 1–6: Category fallback heuristic.
- Days 7–13: Blend (50% moving average + 50% category fallback).
- Day 14+: Full trained ML model.

### Challenge 02: Market Basket Association Analysis
Kirana owners want to know which products sell together to bundle promotions.
Using **Association Rule Mining** (Support, Confidence, Lift):
$$\text{Support}(A \to B) = P(A \cap B)$$
$$\text{Confidence}(A \to B) = \frac{P(A \cap B)}{P(A)}$$
$$\text{Lift}(A \to B) = \frac{P(A \cap B)}{P(A) \cdot P(B)}$$
*Rule of thumb:* A Lift $> 1.5$ indicates significant cross-purchase affinity (e.g. Chai Patti + Sugar, Maggie + Ketchup).

---

## 6. Implementation Deliverables & Acceptance Criteria

1. **`features.py`**: Clean, reproducible feature generation pipeline from processed sales data.
2. **`forecasting.py`**:
   - Baseline Model: 7-day Naive Rolling Mean.
   - Ridge Linear Regression.
   - Random Forest Regressor.
   - LightGBM Regressor.
   - Walk-forward backtesting evaluator outputting WAPE, MAE, and Bias.
3. **`anomaly.py`**: Isolation Forest & Rolling Z-Score detector flagging unusual spikes or zero sales.
4. **`association.py`**: Association rule engine identifying top co-purchased bundles.
5. **`inventory_opt.py`**: Reorder point (ROP) & safety stock engine converting forecasts into suggested purchase orders.
6. **`tests/test_ml.py`**: Automated tests verifying feature dimensions, no lookahead bias, and positive ROP outputs.
7. **`run_phase_2.py`**: One-click benchmark runner generating model comparison tables and charts.
