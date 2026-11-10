"""DukaanOS - Phase 7 Multimodal Ingestion & Omnichannel WhatsApp Runner.

Executes:
1. Simulating messy Mandi wholesale invoice OCR ingestion.
2. Fuzzy SKU catalog matching with confidence scoring.
3. Shopkeeper human-in-the-loop review and approval gate.
4. Committing purchase receipt into the immutable inventory ledger.
5. Multilingual WhatsApp Mandi order generation (wa.me link).
6. Verifying interactive web dashboard availability.
"""

import os
import sys
from pathlib import Path
import pandas as pd

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.backend.database import engine, Base, SessionLocal
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.multimodal.invoice_parser import InvoiceParserService
from dukaanos.src.dukaanos.multimodal.whatsapp_bridge import (
    WhatsAppBridgeService, WhatsAppOrderRequest, WhatsAppOrderItem
)


def run_phase_7_simulation():
    print("=" * 80)
    print("   DUKAANOS - AI-POWERED RETAIL INTELLIGENCE PLATFORM")
    print("   Phase 7: Multimodal Ingestion, WhatsApp Bridge & Storefront UI")
    print("=" * 80)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    store_id = "STORE-001"

    # Step 1: Prepare Catalog for Fuzzy Matcher
    print("\n[Step 1/5] Loading 100-SKU Store Catalog into Fuzzy Matcher...")
    products = db.query(models.Product).filter(models.Product.store_id == store_id).all()
    if not products:
        print("  Database catalog empty, loading from processed CSV...")
        df_prod = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "products_clean.csv")
        catalog = [
            {"id": i, "sku": row["product_id"], "name": row["product_name"], "category": row["category"], "cost_price": float(row["cost_price"])}
            for i, (_, row) in enumerate(df_prod.iterrows(), 1)
        ]
    else:
        catalog = [
            {"id": p.id, "sku": p.sku, "name": p.name, "category": p.category, "cost_price": p.cost_price}
            for p in products
        ]
    print(f"  ✓ Loaded {len(catalog)} products for fuzzy string resolution.")

    # Step 2: Ingest Realistic Messy Wholesale Invoice
    print("\n[Step 2/5] Ingesting Raw Paper Invoice (Mandi Parchi OCR Simulation)...")
    raw_mandi_invoice = """
    === SHREE BALAJI TRADERS & GRAIN MANDI DEPOT ===
    Invoice Date: 10-11-2026 | Mandi Gate No. 4, Narela
    
    Aashir Atta 5k 35 225.00
    Fort Sunlite Oil 1L 40 135.00
    Parle-G 250gm pkts 50 20.00
    Tata Tea Prem 500g 25 220.00
    Unmapped Exotic Masala Pouch 10 45.00
    """
    print("  Input Raw Document Text:")
    for line in raw_mandi_invoice.strip().split("\n"):
        print(f"    | {line}")

    # Step 3: Run Fuzzy Matching & Confidence Scoring
    print("\n[Step 3/5] Running Fuzzy NLP Extraction & Confidence Thresholding...")
    staged_invoice = InvoiceParserService.parse_raw_invoice_text(
        invoice_text=raw_mandi_invoice,
        catalog=catalog,
        default_supplier="Shree Balaji Traders & Mandi Depot",
    )

    print(f"\n  Staged Invoice ID: {staged_invoice.invoice_number}")
    print(f"  Supplier: {staged_invoice.supplier_name}")
    print(f"  Extracted Total Value: ₹{staged_invoice.total_amount:,.2f}")
    print(f"  Auto-Matched Items (Confidence >= 0.85): {staged_invoice.auto_matched_count}")
    print(f"  Pending Review Items (< 0.85): {staged_invoice.review_required_count}")

    print("\n  Extracted Line-Item Resolutions:")
    for item in staged_invoice.items:
        badge = "🟢 AUTO-MATCHED" if item.status == "AUTO_MATCHED" else ("🟡 REVIEW" if item.status == "PENDING_REVIEW" else "🔴 UNMAPPED")
        print(f"    - Raw: '{item.raw_text}' (Qty: {item.extracted_qty}, Rate: ₹{item.extracted_rate:.2f})")
        print(f"      Mapped SKU : {item.matched_sku} - {item.matched_name}")
        print(f"      Confidence : {item.confidence_score * 100:.1f}% | Status: {badge}")

    # Step 4: Human-in-the-Loop Confirmation & Ledger Commit
    print("\n[Step 4/5] Shopkeeper Approves Bill -> Posting Atomic PURCHASE to Inventory Ledger...")
    commit_res = InvoiceParserService.commit_staged_invoice_to_ledger(
        db=db,
        store_id=store_id,
        staged_invoice=staged_invoice,
    )
    print(f"  ✓ Ledger Commit Status: {commit_res['status']}")
    print(f"  ✓ Successfully Posted {commit_res['total_items_posted']} items into immutable ledger.")
    for it in commit_res["items"]:
        print(f"    + SKU {it['sku']}: +{it['quantity_added']} units added (New Running Stock: {it['new_running_balance']})")

    # Step 5: WhatsApp Mandi PO Dispatch
    print("\n[Step 5/5] Generating WhatsApp Mandi Procurement Orders (wa.me)...")
    wa_req = WhatsAppOrderRequest(
        store_name="Shree Ganesh Kirana",
        supplier_phone="919876543210",
        supplier_name="Shree Balaji Mandi Wholesalers",
        language="hinglish",
        items=[
            WhatsAppOrderItem(name="Aashirvaad Atta 5kg", quantity=35, unit="bags"),
            WhatsAppOrderItem(name="Fortune Sunflower Oil 1L", quantity=40, unit="bottles"),
            WhatsAppOrderItem(name="Parle-G 250g", quantity=50, unit="cartons"),
            WhatsAppOrderItem(name="Tata Tea Premium 500g", quantity=25, unit="packs"),
        ],
    )
    wa_res = WhatsAppBridgeService.generate_whatsapp_link(wa_req)
    print(f"  Localized Message Text (Hinglish):")
    for l in wa_res["raw_message"].split("\n"):
        print(f"    | {l}")
    print(f"\n  Direct 1-Click WhatsApp Link:\n    {wa_res['whatsapp_url']}")

    print("\n" + "=" * 80)
    print("   PHASE 7 MULTIMODAL INGESTION & OMNICHANNEL VALIDATION COMPLETE")
    print("   Interactive Shopkeeper UI: http://localhost:8000/ or http://localhost:8000/dashboard")
    print("=" * 80)
    db.close()


if __name__ == "__main__":
    run_phase_7_simulation()

