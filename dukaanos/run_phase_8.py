"""DukaanOS - Phase 8 Offline Edge Sync & AI Khata Intelligence Runner.

Executes:
1. Simulating 4G network outage at the Kirana store.
2. Buffering offline counter sales in an edge replay queue.
3. Network restoration & idempotent batch reconciliation.
4. Demonstrating zero duplicate inventory deductions on replay.
5. Evaluating AI Khata credit default risk scores across 3 customer profiles.
6. Generating culturally respectful WhatsApp payment reminders with UPI QR links.
"""

import os
import sys
from pathlib import Path

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.backend.database import engine, Base, SessionLocal
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.edge.sync_service import (
    EdgeSyncService, BatchSyncRequest, OfflineSalePayload, OfflineTransactionItem
)
from dukaanos.src.dukaanos.khata.credit_service import (
    CreditService, CustomerCreditProfile
)


def run_phase_8_simulation():
    print("=" * 80)
    print("   DUKAANOS - AI-POWERED RETAIL INTELLIGENCE PLATFORM")
    print("   Phase 8: Offline-First Edge Sync & AI Khata Credit Intelligence")
    print("=" * 80)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    store_id = "STORE-001"

    # Step 1: Baseline Stock Verification
    print("\n[Step 1/5] Checking Baseline Inventory Ledger for Target SKU...")
    product = db.query(models.Product).filter(models.Product.store_id == store_id).first()
    if not product:
        # Create test product if missing
        product = models.Product(
            store_id=store_id, sku="STP-001", name="Aashirvaad Atta 5kg",
            category="Staples & Grains", cost_price=225.0, selling_price=245.0,
            min_reorder_level=20, lead_time_days=2,
        )
        db.add(product)
        db.flush()
        InventoryService.post_ledger_event(
            db=db, store_id=store_id, product_id=product.id, event_type="OPENING_STOCK",
            quantity_change=50, unit_cost=225.0, reference_id="INIT-BOOTSTRAP",
        )

    initial_stock = InventoryService.get_current_stock(db, store_id, product.id)
    print(f"  Target SKU: {product.sku} ({product.name})")
    print(f"  Initial Running Ledger Balance: {initial_stock} units")

    # Step 2: Simulate Offline Counter Sales During Network Dropout
    print("\n[Step 2/5] Simulating 4G Dropout: Buffering 3 Sales in Local Replay Queue...")
    offline_txs = [
        OfflineSalePayload(
            sync_id="OFFLINE-TX-001",
            store_id=store_id,
            idempotency_key="IDEMP-EDGE-SIM-001",
            offline_timestamp="2026-11-10T14:15:00Z",
            payment_method="CASH",
            items=[OfflineTransactionItem(product_id=product.id, quantity=2)],
        ),
        OfflineSalePayload(
            sync_id="OFFLINE-TX-002",
            store_id=store_id,
            idempotency_key="IDEMP-EDGE-SIM-002",
            offline_timestamp="2026-11-10T14:18:00Z",
            payment_method="UPI",
            items=[OfflineTransactionItem(product_id=product.id, quantity=3)],
        ),
        OfflineSalePayload(
            sync_id="OFFLINE-TX-003",
            store_id=store_id,
            idempotency_key="IDEMP-EDGE-SIM-003",
            offline_timestamp="2026-11-10T14:22:00Z",
            payment_method="KHATA",
            items=[OfflineTransactionItem(product_id=product.id, quantity=1)],
        ),
    ]

    print(f"  ✓ Buffered {len(offline_txs)} offline sales (Total Units: 6, Total Value: ₹{6 * product.selling_price:,.2f})")
    print("    - TX 1: 2 units (CASH)")
    print("    - TX 2: 3 units (UPI)")
    print("    - TX 3: 1 unit  (UDHAR / KHATA)")

    # Step 3: Network Restored - Batch Sync Reconciliation
    print("\n[Step 3/5] Internet Restored: Reconciling Batch with Central Server...")
    batch_req = BatchSyncRequest(store_id=store_id, client_version="1.0-edge", transactions=offline_txs)
    sync_res = EdgeSyncService.reconcile_batch(db=db, batch=batch_req)

    print(f"  Batch Sync Result:")
    print(f"    Total Received     : {sync_res.total_received}")
    print(f"    Successfully Posted: {sync_res.processed_count}")
    print(f"    Deduplicated (Dupes): {sync_res.deduplicated_count}")

    post_sync_stock = InventoryService.get_current_stock(db, store_id, product.id)
    print(f"  ✓ Updated Ledger Balance: {post_sync_stock} units (Exact deduction: {initial_stock} - 6 = {initial_stock - 6})")

    # Step 4: Verify Idempotency on Network Retries (Replay Attack Protection)
    print("\n[Step 4/5] Re-submitting Same Batch to Verify Idempotency Protection...")
    replay_res = EdgeSyncService.reconcile_batch(db=db, batch=batch_req)
    print(f"  Replay Result:")
    print(f"    Newly Processed : {replay_res.processed_count}")
    print(f"    Deduplicated    : {replay_res.deduplicated_count} (100% blocked from double-charging)")
    stock_after_replay = InventoryService.get_current_stock(db, store_id, product.id)
    assert stock_after_replay == post_sync_stock
    print(f"  ✓ Zero Ledger Drift Confirmed! Stock remains {stock_after_replay} units.")

    # Step 5: AI Khata Credit Default Risk Scoring & Recovery
    print("\n[Step 5/5] Evaluating AI Khata Customer Credit Risk & Generating Reminders...")
    customers = [
        CustomerCreditProfile(
            customer_id=101, name="Sharma Ji", phone="919876543210", credit_limit=5000.0,
            current_balance=850.0, days_overdue=3, successful_repayments_count=6,
        ),
        CustomerCreditProfile(
            customer_id=102, name="Verma Ji", phone="919876543211", credit_limit=5000.0,
            current_balance=2950.0, days_overdue=19, successful_repayments_count=2,
        ),
        CustomerCreditProfile(
            customer_id=103, name="Gupta Ji", phone="919876543212", credit_limit=4000.0,
            current_balance=3900.0, days_overdue=42, successful_repayments_count=0,
        ),
    ]

    print("\n  Customer Credit Risk Evaluations:")
    for cust in customers:
        risk = CreditService.evaluate_credit_risk(cust)
        badge = "🟢 LOW RISK" if risk.risk_tier == "LOW" else ("🟡 MODERATE RISK" if risk.risk_tier == "MODERATE" else "🔴 HIGH RISK (FREEZE)")
        print(f"    - {risk.name}: Balance ₹{risk.current_balance:,.2f} / ₹{risk.credit_limit:,.2f} ({risk.credit_utilization_pct}%)")
        print(f"      Overdue: {risk.days_overdue} days | Risk Score: {risk.risk_score * 100:.1f}% [{badge}]")
        print(f"      Recommendation: {risk.recommended_action}")

    # Generate WhatsApp UPI payment reminder for moderate risk customer
    print("\n  Culturally Polite WhatsApp Payment Reminder Generated for Verma Ji:")
    reminder = CreditService.generate_payment_reminder(
        profile=customers[1],
        store_name="Shree Ganesh Kirana",
        upi_vpa="rameshkirana@upi",
        language="hinglish",
    )
    for l in reminder["raw_message"].split("\n"):
        print(f"    | {l}")
    print(f"\n  Direct WhatsApp wa.me Link:\n    {reminder['whatsapp_url']}")

    print("\n" + "=" * 80)
    print("   PHASE 8 OFFLINE EDGE SYNC & AI KHATA VALIDATION COMPLETE")
    print("=" * 80)
    db.close()


if __name__ == "__main__":
    run_phase_8_simulation()

