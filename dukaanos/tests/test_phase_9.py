"""Automated Test Suite for Phase 9: Federated Mandi Price Intelligence & Group Buying Syndicate."""

import pytest
from dukaanos.src.dukaanos.syndicate.mandi_intelligence import (
    MandiIntelligenceService, WholesalePurchaseRecord, StoreReorderDemand
)


@pytest.fixture
def sample_wholesale_records():
    """Sample privacy-preserving wholesale purchase records from 7 neighboring Kiranas."""
    return [
        WholesalePurchaseRecord(store_id="STORE-001", sku="OIL-003", product_name="Fortune Sunflower Oil 1L", unit_purchase_cost=142.0, quantity_purchased=40, purchase_date="2026-11-01"),
        WholesalePurchaseRecord(store_id="STORE-002", sku="OIL-003", product_name="Fortune Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=60, purchase_date="2026-11-02"),
        WholesalePurchaseRecord(store_id="STORE-003", sku="OIL-003", product_name="Fortune Sunflower Oil 1L", unit_purchase_cost=133.5, quantity_purchased=50, purchase_date="2026-11-03"),
        WholesalePurchaseRecord(store_id="STORE-004", sku="OIL-003", product_name="Fortune Sunflower Oil 1L", unit_purchase_cost=135.0, quantity_purchased=30, purchase_date="2026-11-04"),
        WholesalePurchaseRecord(store_id="STORE-005", sku="OIL-003", product_name="Fortune Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=45, purchase_date="2026-11-05"),
        WholesalePurchaseRecord(store_id="STORE-006", sku="OIL-003", product_name="Fortune Sunflower Oil 1L", unit_purchase_cost=131.0, quantity_purchased=80, purchase_date="2026-11-06"),
        WholesalePurchaseRecord(store_id="STORE-007", sku="OIL-003", product_name="Fortune Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=50, purchase_date="2026-11-07"),
    ]


def test_federated_mandi_benchmark_calculation(sample_wholesale_records):
    """Verifies privacy-preserving wholesale price quantile calculations."""
    benchmark = MandiIntelligenceService.compute_benchmark(
        records=sample_wholesale_records,
        target_sku="OIL-003",
        cluster="DELHI-NCR-NORTH",
    )

    assert benchmark is not None
    assert benchmark.sample_records_count == 7
    assert benchmark.min_rate == 131.0
    assert benchmark.max_rate == 142.0
    assert benchmark.median_rate == 134.0
    assert benchmark.p25_rate <= benchmark.median_rate <= benchmark.p75_rate


def test_overpaying_alert_thresholds(sample_wholesale_records):
    """Verifies that rates > 5% above Mandi median trigger price gouging alerts."""
    benchmark = MandiIntelligenceService.compute_benchmark(
        records=sample_wholesale_records,
        target_sku="OIL-003",
        cluster="DELHI-NCR-NORTH",
    )

    # 1. Store A paying ₹142.00 (Mandi median is ₹134.00 -> +5.97% gap) -> OVERPAYING_ALERT
    alert_high = MandiIntelligenceService.audit_store_price(
        store_purchase_rate=142.0,
        benchmark=benchmark,
    )
    assert alert_high.status == "OVERPAYING_ALERT"
    assert alert_high.price_gap_pct > 5.0
    assert "₹134.00" in alert_high.recommended_talking_point

    # 2. Store B paying ₹134.00 (Equal to median -> 0% gap) -> FAIR_DEAL
    alert_fair = MandiIntelligenceService.audit_store_price(
        store_purchase_rate=134.0,
        benchmark=benchmark,
    )
    assert alert_fair.status == "FAIR_DEAL"
    assert alert_fair.price_gap_pct <= 2.0


def test_syndicate_demand_pooling_and_savings():
    """Verifies multi-store order pooling, Tier-1 bulk discount unlock, and pro-rata savings distribution."""
    demands = [
        StoreReorderDemand(store_id="STORE-001", store_name="Shree Ganesh Kirana", quantity=35, standard_quoted_rate=225.0),
        StoreReorderDemand(store_id="STORE-002", store_name="MahaLaxmi Provision", quantity=40, standard_quoted_rate=228.0),
        StoreReorderDemand(store_id="STORE-003", store_name="Balaji Daily Mart", quantity=50, standard_quoted_rate=226.0),
    ]

    syndicate = MandiIntelligenceService.create_syndicate_pool(
        sku="STP-001",
        product_name="Aashirvaad Shudh Chakki Atta 5kg",
        cluster="DELHI-NCR-NORTH",
        store_demands=demands,
        bulk_tier_threshold=100,  # 125 units pooled >= 100 -> unlocks tier
        bulk_discount_pct=0.08,    # 8% bulk discount
    )

    assert syndicate.total_pooled_units == 125
    assert syndicate.bulk_discount_tier_unlocked is True
    assert syndicate.total_savings_inr > 0
    assert len(syndicate.store_allocations) == 3

    # Verify mathematical conservation of cost savings across all stores
    sum_individual_savings = sum(a["savings_inr"] for a in syndicate.store_allocations)
    assert round(sum_individual_savings, 2) == round(syndicate.total_savings_inr, 2)
