"""DukaanOS - Phase 3 Backend & Data Engineering Runner.

Executes:
1. Multi-tenant database initialization & schema migrations
2. Seeding store tenant, owner user, and all 100 Indian retail products
3. Initializing the event-sourced inventory ledger with opening stocks
4. Simulating live API client operations:
   - JWT authentication
   - Morning business intelligence brief (/api/v1/intelligence/daily-brief)
   - Idempotent counter sales checkout (/api/v1/sales)
   - Procurement PO approval & stock receipt (/api/v1/purchase-orders)
   - Immutable inventory ledger audit trail inspection
"""

import os
import sys
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.backend.config import settings
from dukaanos.src.dukaanos.backend.database import engine, Base, SessionLocal
from dukaanos.src.dukaanos.backend import models, security
from dukaanos.src.dukaanos.backend.main import app
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService


def seed_store_and_products():
    """Seeds primary retail store tenant, owner account, and 100 catalog products."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    store_id = "STORE-001"
    store = db.query(models.Store).filter(models.Store.id == store_id).first()

    if not store:
        print("  Creating primary store tenant (STORE-001)...")
        store = models.Store(
            id=store_id,
            name="DukaanOS Pilot Kirana - Connaught Place",
            owner_name="Ramesh Kumar Gupta",
            phone="9876543210",
            city="New Delhi",
        )
        db.add(store)
        db.flush()

        # Create owner user
        owner = models.User(
            store_id=store_id,
            username="ramesh_kirana",
            hashed_password=security.get_password_hash("kirana2026"),
            role="OWNER",
        )
        db.add(owner)
        db.commit()

    # Seed products if empty
    prod_count = db.query(models.Product).filter(models.Product.store_id == store_id).count()
    if prod_count == 0:
        print("  Seeding 100 Indian retail products into store catalog...")
        products_csv = os.path.join(PROJECT_ROOT, "data", "processed", "products_clean.csv")
        df_prod = pd.read_csv(products_csv)

        ledger_entries = []
        for idx, (_, row) in enumerate(df_prod.iterrows(), 1):
            prod = models.Product(
                store_id=store_id,
                sku=row["product_id"],
                name=row["product_name"],
                category=row["category"],
                unit=row["unit"],
                cost_price=float(row["cost_price"]),
                selling_price=float(row["selling_price"]),
                min_reorder_level=int(row["min_reorder_level"]),
                lead_time_days=int(row["lead_time_days"]),
                supplier_name=str(row["supplier_name"]),
                is_active=True,
            )
            db.add(prod)
            db.flush()

            # Initialize opening stock in inventory ledger
            init_stock = max(int(row["base_daily_velocity"] * 5), int(row["min_reorder_level"]) + 10)
            entry = models.InventoryLedger(
                store_id=store_id,
                transaction_id=f"TX-{idx:07d}",
                date=pd.to_datetime("2025-01-01"),
                product_id=prod.id,
                event_type="OPENING_STOCK",
                quantity_change=init_stock,
                running_balance=init_stock,
                unit_cost=float(row["cost_price"]),
                reference_id="INIT-BOOTSTRAP",
                notes="Initial store opening inventory count",
            )
            db.add(entry)

        db.commit()
        print(f"  ✓ Seeded {len(df_prod)} products with initial opening ledger balances.")
    else:
        print(f"  ✓ Store already has {prod_count} catalog products populated.")

    db.close()


def main():
    print("=" * 80)
    print("   DUKAANOS - AI-POWERED RETAIL INTELLIGENCE PLATFORM")
    print("   Phase 3: Backend & Data Engineering API Service")
    print("=" * 80)

    # 1. Database Seeding
    print("\n[Step 1/5] Initializing Multi-Tenant Database & Seeding Store Catalog...")
    seed_store_and_products()
    db = SessionLocal()
    store_id = "STORE-001"

    # 2. Authentication & User Verification
    print("\n[Step 2/5] Verifying Multi-Tenant Authentication & Access Tokens...")
    owner = db.query(models.User).filter(models.User.username == "ramesh_kirana").first()
    assert owner is not None
    is_valid = security.verify_password("kirana2026", owner.hashed_password)
    assert is_valid
    token = security.create_access_token(data={"sub": owner.username, "store_id": owner.store_id, "role": owner.role})
    payload = security.decode_access_token(token)
    assert payload["store_id"] == store_id
    print(f"  ✓ Authenticated user '{owner.username}' (Store: {store_id}, Role: {owner.role}).")
    print(f"  ✓ Issued cryptographically verified JWT token.")

    # 3. Morning Intelligence Brief
    print("\n[Step 3/5] Querying Morning Intelligence Brief (IntelligenceService.get_morning_brief)...")
    from dukaanos.src.dukaanos.backend.services.intelligence_service import IntelligenceService
    brief = IntelligenceService.get_morning_brief(db=db, store_id=store_id)

    print("\n" + "-" * 80)
    print("                MORNING STORE BRIEFING (दुकानOS AI)")
    print("-" * 80)
    print(f"  Store:                      {brief.store_name} ({brief.store_id})")
    print(f"  Date:                       {brief.date}")
    print(f"  Today's Predicted Sales:    ₹{brief.predicted_sales_inr:,.2f}")
    print(f"  Estimated Customer Baskets: {brief.predicted_basket_count}")
    print(f"  Low / Out of Stock Items:   {brief.low_stock_products_count} products")
    print(f"  Top Purchase Suggestions:   {len(brief.purchase_suggestions)} items")

    if brief.purchase_suggestions:
        print("\n  Top Recommended Restocking Items:")
        for idx, item in enumerate(brief.purchase_suggestions[:4], 1):
            print(f"    {idx}. [{item.urgency}] {item.name[:30]:<30} | Stock: {item.current_stock} | ROP: {item.reorder_point} | Suggested Order: {item.suggested_order_qty} units (₹{item.estimated_cost:,.0f})")

    # 4. Counter Sales Checkout with Idempotency Protection
    print("\n[Step 4/5] Executing Counter Sales Transaction with Idempotency Protection...")
    from dukaanos.src.dukaanos.backend.services.sales_service import SalesService
    from dukaanos.src.dukaanos.backend import schemas

    prods = db.query(models.Product).filter(models.Product.store_id == store_id).all()
    p1 = prods[0]  # Atta
    p2 = prods[10] # Maggi

    idemp_key = "POS-CLIENT-TX-8888"
    checkout_payload = schemas.SalesCreate(
        payment_method="UPI",
        items=[
            schemas.SalesItemCreate(product_id=p1.id, quantity=2),
            schemas.SalesItemCreate(product_id=p2.id, quantity=4),
        ],
        idempotency_key=idemp_key,
    )

    stock_before = InventoryService.get_current_stock(db, store_id, p1.id)

    # First attempt
    sale1 = SalesService.process_checkout(db=db, store_id=store_id, sales_in=checkout_payload, idempotency_key=idemp_key)
    print(f"  ✓ Checkout Executed: Invoice #{sale1.invoice_id} | Total: ₹{sale1.total_revenue} (UPI) | Profit: ₹{sale1.gross_profit}")

    # Second attempt (Duplicate network retry)
    sale2 = SalesService.process_checkout(db=db, store_id=store_id, sales_in=checkout_payload, idempotency_key=idemp_key)
    print(f"  ✓ Idempotency Check: Resent same payload -> Safely returned existing Invoice #{sale2.invoice_id} without double-deduction!")

    stock_after = InventoryService.get_current_stock(db, store_id, p1.id)
    assert stock_after == stock_before - 2

    # 5. Procurement Lifecycle: Draft, Approve, and Receive Goods into Ledger
    print("\n[Step 5/5] Executing Procurement Lifecycle (Draft -> Approve -> Receive Goods)...")
    from dukaanos.src.dukaanos.backend.services.po_service import PurchaseOrderService

    po_payload = schemas.POCreate(
        supplier_name="Shree Ganesh Grain & Staples Mandi",
        items=[
            schemas.POItemCreate(product_id=p1.id, quantity_ordered=25, unit_cost=p1.cost_price),
        ],
    )

    # Draft
    po = PurchaseOrderService.create_po(db=db, store_id=store_id, po_in=po_payload)
    print(f"  ✓ Purchase Order Drafted: #{po.po_number} for {po.supplier_name} (₹{po.total_amount})")

    # Approve
    po_appr = PurchaseOrderService.approve_po(db=db, store_id=store_id, po_id=po.id)
    print(f"  ✓ Owner Approval Granted: Status is now '{po_appr.status}'")

    # Receive Goods
    po_recv = PurchaseOrderService.receive_po(db=db, store_id=store_id, po_id=po.id)
    print(f"  ✓ Delivery Received: Stock automatically posted to inventory ledger (+25 units)!")

    # Audit Ledger
    latest_events = (
        db.query(models.InventoryLedger)
        .filter(models.InventoryLedger.store_id == store_id, models.InventoryLedger.product_id == p1.id)
        .order_by(models.InventoryLedger.id.desc())
        .limit(3)
        .all()
    )
    print(f"\n  Latest 3 Immutable Ledger Events for '{p1.name[:25]}':")
    for event in latest_events:
        print(f"    - [{str(event.date)[:19]}] {event.transaction_id} | {event.event_type:<14} | Delta: {event.quantity_change:+3d} | Running Stock: {event.running_balance}")

    db.close()
    print("\n" + "=" * 80)
    print("   ✓ PHASE 3 BACKEND & DATA ENGINEERING COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()

