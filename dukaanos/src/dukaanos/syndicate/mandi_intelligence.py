"""Federated Mandi Price Intelligence & Group Buying Syndicate Engine.

Implements:
1. Privacy-preserving wholesale price aggregation across distributed store tenants.
2. Mandi Overpaying Detection & Arbitrage Alerting.
3. Collective Group Buying (Syndicate PO) pooling & pro-rata savings allocation.
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WholesalePurchaseRecord(BaseModel):
    store_id: str
    sku: str
    product_name: str
    unit_purchase_cost: float
    quantity_purchased: int
    purchase_date: str
    mandi_cluster: str = "DELHI-NCR-NORTH"


class MandiPriceBenchmark(BaseModel):
    sku: str
    product_name: str
    mandi_cluster: str
    sample_records_count: int
    min_rate: float
    p25_rate: float
    median_rate: float
    p75_rate: float
    max_rate: float
    last_updated: str


class OverpayingAlert(BaseModel):
    sku: str
    product_name: str
    store_purchase_rate: float
    mandi_median_rate: float
    price_gap_pct: float
    status: str  # 'FAIR_DEAL', 'MILDLY_ELEVATED', 'OVERPAYING_ALERT'
    recommended_talking_point: str


class StoreReorderDemand(BaseModel):
    store_id: str
    store_name: str
    quantity: int
    standard_quoted_rate: float


class SyndicateGroupOrder(BaseModel):
    syndicate_id: str
    sku: str
    product_name: str
    mandi_cluster: str
    total_participating_stores: int
    total_pooled_units: int
    bulk_discount_tier_unlocked: bool
    standard_total_cost: float
    syndicate_bulk_rate: float
    syndicate_total_cost: float
    total_savings_inr: float
    store_allocations: List[Dict[str, Any]]


class MandiIntelligenceService:
    """Manages federated wholesale benchmarking, overpaying detection, and group buying."""

    @staticmethod
    def compute_benchmark(
        records: List[WholesalePurchaseRecord],
        target_sku: str,
        cluster: str = "DELHI-NCR-NORTH",
    ) -> Optional[MandiPriceBenchmark]:
        """Calculates privacy-preserving wholesale price quantiles across multiple stores."""
        filtered = [r for r in records if r.sku == target_sku and r.mandi_cluster == cluster]
        if not filtered:
            return None

        rates = [r.unit_purchase_cost for r in filtered]
        p_name = filtered[0].product_name

        return MandiPriceBenchmark(
            sku=target_sku,
            product_name=p_name,
            mandi_cluster=cluster,
            sample_records_count=len(rates),
            min_rate=round(float(np.min(rates)), 2),
            p25_rate=round(float(np.percentile(rates, 25)), 2),
            median_rate=round(float(np.median(rates)), 2),
            p75_rate=round(float(np.percentile(rates, 75)), 2),
            max_rate=round(float(np.max(rates)), 2),
            last_updated=datetime.now().strftime("%Y-%m-%d"),
        )

    @staticmethod
    def audit_store_price(
        store_purchase_rate: float,
        benchmark: MandiPriceBenchmark,
    ) -> OverpayingAlert:
        """Compares a storekeeper's invoice purchase rate against local Mandi benchmark."""
        med = benchmark.median_rate
        gap_pct = ((store_purchase_rate - med) / med) * 100.0

        if gap_pct > 5.0:
            status = "OVERPAYING_ALERT"
            talking_point = (
                f"Bhaiya, {benchmark.mandi_cluster} mandi me {benchmark.sample_records_count} dukaane "
                f"{benchmark.product_name} ₹{med:.2f} me kharid rahi hain. "
                f"Aap humse ₹{store_purchase_rate:.2f} kyu le rahe ho? Rate kam karo!"
            )
        elif gap_pct > 2.0:
            status = "MILDLY_ELEVATED"
            talking_point = (
                f"Rate is slightly above local median of ₹{med:.2f}. "
                f"Consider renegotiating payment terms with distributor."
            )
        else:
            status = "FAIR_DEAL"
            talking_point = (
                f"Your purchase price of ₹{store_purchase_rate:.2f} is competitive with Mandi rates."
            )

        return OverpayingAlert(
            sku=benchmark.sku,
            product_name=benchmark.product_name,
            store_purchase_rate=round(store_purchase_rate, 2),
            mandi_median_rate=med,
            price_gap_pct=round(gap_pct, 1),
            status=status,
            recommended_talking_point=talking_point,
        )

    @staticmethod
    def create_syndicate_pool(
        sku: str,
        product_name: str,
        cluster: str,
        store_demands: List[StoreReorderDemand],
        bulk_tier_threshold: int = 100,
        bulk_discount_pct: float = 0.08,  # 8% bulk distributor discount
    ) -> SyndicateGroupOrder:
        """Pools multi-store reorders into a consolidated syndicate purchase order with pro-rata savings."""
        total_units = sum(d.quantity for d in store_demands)
        tier_unlocked = total_units >= bulk_tier_threshold

        avg_standard_rate = float(np.mean([d.standard_quoted_rate for d in store_demands]))
        syndicate_bulk_rate = round(avg_standard_rate * (1.0 - bulk_discount_pct), 2) if tier_unlocked else avg_standard_rate

        standard_total = sum(d.quantity * d.standard_quoted_rate for d in store_demands)
        syndicate_total = sum(d.quantity * syndicate_bulk_rate for d in store_demands)
        total_savings = standard_total - syndicate_total

        allocations = []
        for d in store_demands:
            std_cost = d.quantity * d.standard_quoted_rate
            syn_cost = d.quantity * syndicate_bulk_rate
            savings = std_cost - syn_cost
            allocations.append({
                "store_id": d.store_id,
                "store_name": d.store_name,
                "units_allocated": d.quantity,
                "standard_cost": round(std_cost, 2),
                "syndicate_cost": round(syn_cost, 2),
                "savings_inr": round(savings, 2),
            })

        syndicate_id = f"SYN-{cluster[:3]}-{datetime.now().strftime('%Y%m%d%H%M')}"

        return SyndicateGroupOrder(
            syndicate_id=syndicate_id,
            sku=sku,
            product_name=product_name,
            mandi_cluster=cluster,
            total_participating_stores=len(store_demands),
            total_pooled_units=total_units,
            bulk_discount_tier_unlocked=tier_unlocked,
            standard_total_cost=round(standard_total, 2),
            syndicate_bulk_rate=syndicate_bulk_rate,
            syndicate_total_cost=round(syndicate_total, 2),
            total_savings_inr=round(total_savings, 2),
            store_allocations=allocations,
        )

