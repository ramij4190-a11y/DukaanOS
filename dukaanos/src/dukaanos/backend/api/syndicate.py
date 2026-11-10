"""Federated Mandi Price Intelligence & Group Buying Syndicate API Endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from dukaanos.src.dukaanos.syndicate.mandi_intelligence import (
    MandiIntelligenceService, WholesalePurchaseRecord, MandiPriceBenchmark,
    OverpayingAlert, StoreReorderDemand, SyndicateGroupOrder
)

router = APIRouter(prefix="/syndicate", tags=["Mandi Price & Group Buying Syndicate"])


class AuditPriceRequest(BaseModel):
    sku: str
    store_purchase_rate: float
    mandi_cluster: str = "DELHI-NCR-NORTH"


class SyndicatePoolRequest(BaseModel):
    sku: str
    product_name: str
    mandi_cluster: str = "DELHI-NCR-NORTH"
    bulk_tier_threshold: int = 100
    store_demands: List[StoreReorderDemand]


# Simulated in-memory store wholesale purchase records across Delhi-NCR North cluster
SAMPLE_MANDI_RECORDS: List[WholesalePurchaseRecord] = [
    WholesalePurchaseRecord(store_id="STORE-001", sku="OIL-003", product_name="Fortune Sunlite Refined Sunflower Oil 1L", unit_purchase_cost=142.0, quantity_purchased=40, purchase_date="2026-11-01"),
    WholesalePurchaseRecord(store_id="STORE-002", sku="OIL-003", product_name="Fortune Sunlite Refined Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=60, purchase_date="2026-11-02"),
    WholesalePurchaseRecord(store_id="STORE-003", sku="OIL-003", product_name="Fortune Sunlite Refined Sunflower Oil 1L", unit_purchase_cost=133.5, quantity_purchased=50, purchase_date="2026-11-03"),
    WholesalePurchaseRecord(store_id="STORE-004", sku="OIL-003", product_name="Fortune Sunlite Refined Sunflower Oil 1L", unit_purchase_cost=135.0, quantity_purchased=30, purchase_date="2026-11-04"),
    WholesalePurchaseRecord(store_id="STORE-005", sku="OIL-003", product_name="Fortune Sunlite Refined Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=45, purchase_date="2026-11-05"),
    WholesalePurchaseRecord(store_id="STORE-006", sku="OIL-003", product_name="Fortune Sunlite Refined Sunflower Oil 1L", unit_purchase_cost=131.0, quantity_purchased=80, purchase_date="2026-11-06"),
    WholesalePurchaseRecord(store_id="STORE-007", sku="OIL-003", product_name="Fortune Sunlite Refined Sunflower Oil 1L", unit_purchase_cost=134.0, quantity_purchased=50, purchase_date="2026-11-07"),
    WholesalePurchaseRecord(store_id="STORE-001", sku="STP-001", product_name="Aashirvaad Shudh Chakki Atta 5kg", unit_purchase_cost=225.0, quantity_purchased=35, purchase_date="2026-11-01"),
    WholesalePurchaseRecord(store_id="STORE-002", sku="STP-001", product_name="Aashirvaad Shudh Chakki Atta 5kg", unit_purchase_cost=218.0, quantity_purchased=50, purchase_date="2026-11-02"),
    WholesalePurchaseRecord(store_id="STORE-003", sku="STP-001", product_name="Aashirvaad Shudh Chakki Atta 5kg", unit_purchase_cost=215.0, quantity_purchased=60, purchase_date="2026-11-03"),
    WholesalePurchaseRecord(store_id="STORE-004", sku="STP-001", product_name="Aashirvaad Shudh Chakki Atta 5kg", unit_purchase_cost=220.0, quantity_purchased=40, purchase_date="2026-11-04"),
    WholesalePurchaseRecord(store_id="STORE-005", sku="STP-001", product_name="Aashirvaad Shudh Chakki Atta 5kg", unit_purchase_cost=218.0, quantity_purchased=45, purchase_date="2026-11-05"),
]


@router.get("/benchmark", response_model=MandiPriceBenchmark)
def get_mandi_benchmark(
    sku: str = Query(..., example="OIL-003"),
    cluster: str = Query("DELHI-NCR-NORTH", example="DELHI-NCR-NORTH"),
):
    """Calculates privacy-preserving wholesale price benchmark quantiles for an SKU."""
    benchmark = MandiIntelligenceService.compute_benchmark(
        records=SAMPLE_MANDI_RECORDS,
        target_sku=sku,
        cluster=cluster,
    )
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"No wholesale benchmark records found for SKU {sku}")
    return benchmark


@router.post("/audit-price", response_model=OverpayingAlert)
def audit_store_purchase_price(req: AuditPriceRequest):
    """Audits a storekeeper's invoice rate against local Mandi benchmark and returns overpaying alerts."""
    benchmark = MandiIntelligenceService.compute_benchmark(
        records=SAMPLE_MANDI_RECORDS,
        target_sku=req.sku,
        cluster=req.mandi_cluster,
    )
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"No benchmark data found for SKU {req.sku}")

    return MandiIntelligenceService.audit_store_price(
        store_purchase_rate=req.store_purchase_rate,
        benchmark=benchmark,
    )


@router.post("/pool-order", response_model=SyndicateGroupOrder)
def create_group_buying_syndicate(req: SyndicatePoolRequest):
    """Aggregates multi-store reorders into a consolidated syndicate purchase order with pro-rata savings."""
    return MandiIntelligenceService.create_syndicate_pool(
        sku=req.sku,
        product_name=req.product_name,
        cluster=req.mandi_cluster,
        store_demands=req.store_demands,
        bulk_tier_threshold=req.bulk_tier_threshold,
    )

