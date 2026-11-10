"""Automated Test Suite for Phase 8: Offline Edge Sync & AI Khata Credit Intelligence."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dukaanos.src.dukaanos.backend.database import Base
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.edge.sync_service import (
    EdgeSyncService, BatchSyncRequest, OfflineSalePayload, OfflineTransactionItem
)
from dukaanos.src.dukaanos.khata.credit_service import (
    CreditService, CustomerCreditProfile
)


@pytest.fixture(scope="function")
def db_session():
    """Sets up an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_offline_batch_sync_and_idempotency(db_session):
    """Verifies that offline sales batches are reconciled idempotently with zero double deduction."""
    store = models.Store(id="STORE-001", name="Store Delhi", owner_name="Owner A", phone="111", city="Delhi")
    db_session.add(store)
    db_session.flush()

    prod = models.Product(
        store_id="STORE-001",
        sku="STP-001",
        name="Aashirvaad Atta 5kg",
        category="Staples & Grains",
        cost_price=225.0,
        selling_price=245.0,
        min_reorder_level=20,
        lead_time_days=2,
    )
    db_session.add(prod)
    db_session.flush()

    # Initial stock: 50 units
    InventoryService.post_ledger_event(
        db=db_session,
        store_id="STORE-001",
        product_id=prod.id,
        event_type="OPENING_STOCK",
        quantity_change=50,
        unit_cost=225.0,
        reference_id="INIT-TEST",
    )
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 50

    # Build batch with 1 offline transaction (3 units of STP-001)
    batch = BatchSyncRequest(
        store_id="STORE-001",
        transactions=[
            OfflineSalePayload(
                sync_id="SYNC-001",
                store_id="STORE-001",
                idempotency_key="IDEMP-OFFLINE-9999",
                offline_timestamp="2026-11-10T14:00:00Z",
                payment_method="CASH",
                items=[OfflineTransactionItem(product_id=prod.id, quantity=3)],
            )
        ],
    )

    # First sync run: must process and deduct 3 units (50 - 3 = 47)
    res1 = EdgeSyncService.reconcile_batch(db=db_session, batch=batch)
    assert res1.processed_count == 1
    assert res1.deduplicated_count == 0
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 47

    # Second sync run (replay of same batch): must deduplicate and NOT deduct stock again
    res2 = EdgeSyncService.reconcile_batch(db=db_session, batch=batch)
    assert res2.processed_count == 0
    assert res2.deduplicated_count == 1
    assert res2.results[0]["status"] == "DEDUPLICATED"
    # Stock remains 47!
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 47


def test_credit_risk_evaluation_tiers():
    """Verifies customer credit risk scoring across LOW, MODERATE, and HIGH tiers."""
    # 1. Healthy customer (LOW risk)
    low_profile = CustomerCreditProfile(
        customer_id=1,
        name="Sharma Ji",
        phone="9876543210",
        credit_limit=5000.0,
        current_balance=800.0,  # 16% utilization
        days_overdue=2,
        successful_repayments_count=5,
    )
    res_low = CreditService.evaluate_credit_risk(low_profile)
    assert res_low.risk_tier == "LOW"
    assert res_low.risk_score < 0.35

    # 2. Moderate risk customer
    mod_profile = CustomerCreditProfile(
        customer_id=2,
        name="Verma Ji",
        phone="9876543211",
        credit_limit=5000.0,
        current_balance=3000.0,  # 60% utilization
        days_overdue=18,
        successful_repayments_count=2,
    )
    res_mod = CreditService.evaluate_credit_risk(mod_profile)
    assert res_mod.risk_tier == "MODERATE"
    assert 0.35 <= res_mod.risk_score < 0.70

    # 3. High risk customer (Default alert)
    high_profile = CustomerCreditProfile(
        customer_id=3,
        name="Gupta Ji",
        phone="9876543212",
        credit_limit=5000.0,
        current_balance=4800.0,  # 96% utilization
        days_overdue=40,
        successful_repayments_count=0,
    )
    res_high = CreditService.evaluate_credit_risk(high_profile)
    assert res_high.risk_tier == "HIGH"
    assert res_high.risk_score >= 0.70


def test_whatsapp_payment_reminder_upi_link():
    """Verifies that polite payment reminders contain valid UPI QR links."""
    profile = CustomerCreditProfile(
        customer_id=1,
        name="Ramesh Sharma",
        phone="9876543210",
        credit_limit=5000.0,
        current_balance=1450.0,
        days_overdue=15,
        successful_repayments_count=3,
    )

    res = CreditService.generate_payment_reminder(
        profile=profile,
        store_name="Shree Ganesh Kirana",
        upi_vpa="rameshkirana@upi",
        language="hinglish",
    )

    assert "upi://pay?pa=rameshkirana@upi" in res["upi_deep_link"]
    assert "1450.00" in res["upi_deep_link"]
    assert "https://wa.me/9876543210?text=" in res["whatsapp_url"]
    assert "Shree Ganesh Kirana" in res["raw_message"]
    assert "1,450.00" in res["raw_message"]
