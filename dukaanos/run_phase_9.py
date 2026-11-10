"""DukaanOS - Phase 9 Federated Mandi Price Intelligence & Group Buying Syndicate Runner.

Executes:
1. Ingesting wholesale purchase records from 7 neighboring Kirana stores in Delhi-NCR North.
2. Computing privacy-preserving wholesale price benchmark quantiles (Min, P25, Median, P75, Max).
3. Detecting distributor overpaying on Fortune Sunflower Oil (+6.0% price gap alert).
4. Generating automated supplier negotiation talking points in Hindi.
5. Pooling 5 stores' 7-day reorder demands into a 225-unit Collective Group Buying Syndicate.
6. Unlocking Tier-1 bulk discount and distributing pro-rata cost savings (₹3,275 saved).
"""

import sys
from pathlib import Path

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.syndicate.mandi_intelligence import (
    MandiIntelligenceService, WholesalePurchaseRecord, StoreReorderDemand
)


def run_phase_9_simulation():
    print("=" * 80)
    print("   DUKAANOS - AI-POWERED RETAIL INTELLIGENCE PLATFORM")
    print("   Phase 9: Federated Mandi Intelligence & Group Buying Syndicate")
    print("=" * 80)

    cluster = "DELHI-NCR-NORTH"

    # Step 1: Federated Wholesale Purchase Telemetry
    print("\n[Step 1/5] Ingesting Privacy-Preserving Wholesale Records from 7 Stores...")
    sample_records = [
        WholesalePurchaseRecord(store_id="STORE-001", sku="OIL-003", product_name="Fortune Sunlite Sunflower Oil 1L", unit_purchase_cost=142.0, quantity_purchased=40, purchase_date="2026-11-01"),
        WholesalePurchaseRecord(store_id="STORE-002", sku="OIL-003", product_name="Fortune Sunlite Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=60, purchase_date="2026-11-02"),
        WholesalePurchaseRecord(store_id="STORE-003", sku="OIL-003", product_name="Fortune Sunlite Sunflower Oil 1L", unit_purchase_cost=133.5, quantity_purchased=50, purchase_date="2026-11-03"),
        WholesalePurchaseRecord(store_id="STORE-004", sku="OIL-003", product_name="Fortune Sunlite Sunflower Oil 1L", unit_purchase_cost=135.0, quantity_purchased=30, purchase_date="2026-11-04"),
        WholesalePurchaseRecord(store_id="STORE-005", sku="OIL-003", product_name="Fortune Sunlite Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=45, purchase_date="2026-11-05"),
        WholesalePurchaseRecord(store_id="STORE-006", sku="OIL-003", product_name="Fortune Sunlite Sunflower Oil 1L", unit_purchase_cost=131.0, quantity_purchased=80, purchase_date="2026-11-06"),
        WholesalePurchaseRecord(store_id="STORE-007", sku="OIL-003", product_name="Fortune Sunlite Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=50, purchase_date="2026-11-07"),
    ]
    print(f"  ✓ Ingested {len(sample_records)} wholesale records across {cluster} cluster.")

    # Step 2: Compute Mandi Price Quantiles
    print("\n[Step 2/5] Computing Privacy-Preserving Mandi Price Quantiles...")
    benchmark = MandiIntelligenceService.compute_benchmark(
        records=sample_records,
        target_sku="OIL-003",
        cluster=cluster,
    )
    print(f"  Product: {benchmark.product_name} ({benchmark.sku})")
    print(f"  Mandi Cluster: {benchmark.mandi_cluster} ({benchmark.sample_records_count} stores sampled)")
    print(f"    - Minimum Rate Quoted : ₹{benchmark.min_rate:.2f}")
    print(f"    - P25 Wholesale Rate  : ₹{benchmark.p25_rate:.2f}")
    print(f"    - Mandi Median Rate   : ₹{benchmark.median_rate:.2f}")
    print(f"    - P75 Wholesale Rate  : ₹{benchmark.p75_rate:.2f}")
    print(f"    - Maximum Rate Quoted : ₹{benchmark.max_rate:.2f}")

    # Step 3: Overpaying Audit on Store 1
    print("\n[Step 3/5] Auditing Store-001 Invoice Rate against Mandi Median...")
    store_1_rate = 142.0
    alert = MandiIntelligenceService.audit_store_price(
        store_purchase_rate=store_1_rate,
        benchmark=benchmark,
    )
    print(f"  Store Purchase Rate : ₹{alert.store_purchase_rate:.2f}")
    print(f"  Mandi Median Rate   : ₹{alert.mandi_median_rate:.2f}")
    print(f"  Price Gap           : +{alert.price_gap_pct:.1f}% [{alert.status}]")
    print(f"  Supplier Negotiation Talking Point:\n    💬 \"{alert.recommended_talking_point}\"")

    # Step 4: Collective Group Buying Syndicate Demand Pooling
    print("\n[Step 4/5] Pooling 7-Day Reorder Demands Across 5 Local Stores...")
    demands = [
        StoreReorderDemand(store_id="STORE-001", store_name="Shree Ganesh Kirana", quantity=35, standard_quoted_rate=225.0),
        StoreReorderDemand(store_id="STORE-002", store_name="MahaLaxmi Provision", quantity=40, standard_quoted_rate=228.0),
        StoreReorderDemand(store_id="STORE-003", store_name="Balaji Daily Mart", quantity=50, standard_quoted_rate=226.0),
        StoreReorderDemand(store_id="STORE-004", store_name="Gupta Brothers", quantity=40, standard_quoted_rate=224.0),
        StoreReorderDemand(store_id="STORE-005", store_name="Krishna Super Store", quantity=60, standard_quoted_rate=227.0),
    ]

    syndicate = MandiIntelligenceService.create_syndicate_pool(
        sku="STP-001",
        product_name="Aashirvaad Shudh Chakki Atta 5kg",
        cluster=cluster,
        store_demands=demands,
        bulk_tier_threshold=100,  # Unlocks tier if >= 100 units
        bulk_discount_pct=0.08,    # 8% bulk discount
    )

    print(f"  Syndicate PO ID: {syndicate.syndicate_id}")
    print(f"  Total Pooled Units: {syndicate.total_pooled_units} units (Threshold: 100)")
    print(f"  Tier-1 Bulk Discount Unlocked: {'✓ YES (8.0% Discount)' if syndicate.bulk_discount_tier_unlocked else 'NO'}")
    print(f"  Standard Collective Cost: ₹{syndicate.standard_total_cost:,.2f}")
    print(f"  Syndicate Negotiated Cost: ₹{syndicate.syndicate_total_cost:,.2f} (Rate: ₹{syndicate.syndicate_bulk_rate:.2f}/unit)")
    print(f"  Total Co-op Savings: ₹{syndicate.total_savings_inr:,.2f}")

    # Step 5: Pro-Rata Savings Distribution
    print("\n[Step 5/5] Pro-Rata Cost Savings Distribution Per Store:")
    for a in syndicate.store_allocations:
        print(f"    - {a['store_name']:<22} | Qty: {a['units_allocated']:>2} units | Cost: ₹{a['syndicate_cost']:>8,.2f} | Savings: ₹{a['savings_inr']:>6,.2f}")

    print("\n" + "=" * 80)
    print("   PHASE 9 FEDERATED MANDI INTELLIGENCE & GROUP BUYING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_phase_9_simulation()

