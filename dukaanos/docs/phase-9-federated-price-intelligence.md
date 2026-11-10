# Phase 9: Federated Mandi Price Intelligence & Group Buying Syndicate (मंडी भाव और सामूहिक खरीद नेटवर्क)

## 1. Executive Summary & Startup Moat
In the Indian retail ecosystem, individual Kirana shopkeepers suffer from **extreme wholesale price asymmetry**:
- FMCG distributors and Mandi commission agents quote different purchase prices to different shops depending on bargaining power, credit terms, and lack of market transparency.
- A single Kirana ordering 20 bags of Atta gets quoted **₹225/bag**, while a supermarket chain ordering 500 bags gets **₹205/bag** (an 8.9% cost disadvantage).
- Because small retailers operate in isolation, they have zero visibility into what neighboring stores are paying for the exact same SKU.

**Phase 9 transforms DukaanOS from a single-store operating system into a Federated Cooperative Network**:
1. **Federated Wholesale Price Intelligence:** Aggregates anonymized, privacy-preserving wholesale purchase records extracted from invoices across the store network to compute local Mandi benchmark rates.
2. **Overpaying Detection & Mandi Price Alerts:** Notifies shopkeepers whenever their invoice rates exceed the local Mandi median benchmark.
3. **Collective Group Buying (Syndicate PO Engine):** Aggregates predicted 7-day replenishment demands across neighboring stores into consolidated bulk purchase orders, unlocking tier-1 wholesale discounts (+5% to 8% margin boost).

---

## 2. Technical Architecture & Component Flow

```
                      +-----------------------------------------------------------+
                      |         DISTRIBUTED STORE TENANTS (STORE-001 ... 050)     |
                      |  * Store A (Delhi)   * Store B (Noida)   * Store C (Gurugram) |
                      |  * Ingested Paper Invoices & Confirmed Purchase Orders    |
                      +-----------------------------------------------------------+
                                                    |
                                    [Anonymized Wholesale Telemetry]
                                                    v
                      +-----------------------------------------------------------+
                      |       LAYER 1: PRIVACY-PRESERVING PRICE BENCHMARKER       |
                      |  * Strips store identities (Zero competitor leakage)       |
                      |  * Groups by Micro-Mandi Geohash / City Cluster           |
                      |  * Computes Rolling 14-Day Median, P25, and P75 Rates     |
                      +-----------------------------------------------------------+
                                                    |
                                                    v
                      +-----------------------------------------------------------+
                      |       LAYER 2: OVERPAYING DETECTOR & MANDI ARBITRAGE      |
                      |  * Flags supplier price gouging:                          |
                      |    PriceGap = (StoreRate - MandiMedian) / MandiMedian     |
                      |  * Generates supplier negotiation talking points           |
                      +-----------------------------------------------------------+
                                                    |
                                                    v
                      +-----------------------------------------------------------+
                      |       LAYER 3: COLLECTIVE GROUP BUYING (SYNDICATE PO)     |
                      |  * Aggregates 7-day demand across 10-50 local stores      |
                      |  * Volume Tier Trigger: e.g. 500 bags Atta / 200 boxes Oil|
                      |  * Auto-generates Consolidated Syndicate Mandi PO         |
                      |  * Distributes bulk savings (+5% to 8% margin expansion)  |
                      +-----------------------------------------------------------+
```

---

## 3. Engineering Specifications

### 3.1 Federated Wholesale Benchmark Schema
```json
{
  "mandi_cluster": "DELHI-NCR-NORTH",
  "sku": "STP-001",
  "product_name": "Aashirvaad Shudh Chakki Atta 5kg",
  "sample_stores_count": 18,
  "last_updated": "2026-11-10",
  "benchmark_metrics": {
    "min_rate": 208.0,
    "p25_rate": 215.0,
    "median_rate": 218.0,
    "p75_rate": 226.0,
    "max_rate": 238.0
  }
}
```

### 3.2 Overpaying Alert Formulation
When a storekeeper ingests a wholesale invoice with unit rate $P_{\text{store}}$:
$$\Delta P = \frac{P_{\text{store}} - P_{\text{median}}}{P_{\text{median}}} \times 100\%$$
- **FAIR DEAL ($\Delta P \le +2\%$):** Competitive wholesale rate.
- **MILDLY ELEVATED ($+2\% < \Delta P \le +5\%$):** Above median; suggest renegotiating payment terms.
- **OVERPAYING ALERT ($\Delta P > +5\%$):** Price gouging alert; provide Mandi benchmark report to counter distributor.

### 3.3 Collective Group Buying (Syndicate PO) Formulation
For high-velocity staple commodities $k \in \{\text{Atta, Oil, Sugar, Rice}\}$ across cluster stores $S$:
$$Q_{\text{syndicate}} = \sum_{s \in S} \text{SuggestedReorderQty}(s, k)$$
When $Q_{\text{syndicate}} \ge Q_{\text{tier1\_bulk}}$ (e.g. 500 units):
- Unlocks **Tier-1 Manufacturer / Depot Pricing** ($P_{\text{bulk}} \approx P_{\text{median}} \times 0.92$).
- Computes pro-rata savings per store:
  $$\text{Savings}_s = Q_s \times (P_{\text{standard}} - P_{\text{bulk}})$$

---

## 4. Verification & Testing Requirements
1. `test_federated_benchmark_computation`: Verifies median, P25, P75 price quantiles across multiple stores.
2. `test_overpaying_alert_thresholds`: Verifies detection of price gouging vs. fair pricing.
3. `test_collective_group_buying_pooling`: Verifies multi-store demand aggregation and bulk discount tier triggering.
4. `test_pro_rata_savings_distribution`: Confirms mathematical conservation of volume allocations and cost savings.

