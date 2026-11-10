"""Automated Integration Test Suite for DukaanOS Backend & Multi-Tenant Architecture.

Tests:
1. Health check endpoint function
2. Tenant registration and password hashing / JWT token validation
3. Multi-tenant catalog isolation (Store A vs Store B)
4. Idempotent sales checkout preventing double deductions
5. Purchase order lifecycle (DRAFT -> APPROVED -> RECEIVED) updating ledger
6. Morning daily brief intelligence calculations
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dukaanos.src.dukaanos.backend.database import Base
from dukaanos.src.dukaanos.backend import models, security, schemas
from dukaanos.src.dukaanos.backend.main import health_check
from dukaanos.src.dukaanos.backend.services.sales_service import SalesService
from dukaanos.src.dukaanos.backend.services.po_service import PurchaseOrderService
from dukaanos.src.dukaanos.backend.services.intelligence_service import IntelligenceService
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService


@pytest.fixture(scope="function")
def db_session():
    """Sets up an isolated in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_health_check():
    """Verifies service health check response."""
    res = health_check()
    assert res["status"] == "healthy"
    assert "version" in res


def test_store_registration_and_login(db_session):
    """Tests tenant creation and cryptographic JWT token issuance."""
    store = models.Store(
        id="STORE-001",
        name="Shree Ganesh Kirana",
        owner_name="Ramesh Kumar",
        phone="9876543210",
        city="Delhi",
    )
    db_session.add(store)
    db_session.flush()

    hashed_pw = security.get_password_hash("securepassword123")
    user = models.User(
        store_id="STORE-001",
        username="ramesh_owner",
        hashed_password=hashed_pw,
        role="OWNER",
    )
    db_session.add(user)
    db_session.commit()

    # Verify password check
    assert security.verify_password("securepassword123", user.hashed_password)
    assert not security.verify_password("wrongpassword", user.hashed_password)

    # Issue and decode JWT
    token = security.create_access_token({"sub": user.username, "store_id": "STORE-001", "role": user.role})
    payload = security.decode_access_token(token)
    assert payload["sub"] == "ramesh_owner"
    assert payload["store_id"] == "STORE-001"


def test_multi_tenant_isolation(db_session):
    """Challenge 05: Store B must never access or view Store A's catalog or ledger."""
    # Store A setup
    store_a = models.Store(id="STORE-001", name="Store Delhi", owner_name="Owner A", phone="111", city="Delhi")
    store_b = models.Store(id="STORE-002", name="Store Ahmedabad", owner_name="Owner B", phone="222", city="Ahmedabad")
    db_session.add_all([store_a, store_b])
    db_session.flush()

    # Product in Store A
    prod_a = models.Product(
        store_id="STORE-001",
        sku="STP-001",
        name="Aashirvaad Atta 5kg",
        category="Staples & Grains",
        cost_price=225.0,
        selling_price=245.0,
        min_reorder_level=20,
        lead_time_days=2,
    )
    db_session.add(prod_a)
    db_session.commit()

    # Query products scoped to Store A -> returns 1
    items_a = db_session.query(models.Product).filter(models.Product.store_id == "STORE-001").all()
    assert len(items_a) == 1
    assert items_a[0].sku == "STP-001"

    # Query products scoped to Store B -> must be 0 (Strict isolation)
    items_b = db_session.query(models.Product).filter(models.Product.store_id == "STORE-002").all()
    assert len(items_b) == 0


def test_sales_checkout_and_idempotency(db_session):
    """Challenge 03: Idempotent checkout prevents duplicate inventory deductions."""
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

    # Initial stock in ledger
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

    sale_in = schemas.SalesCreate(
        payment_method="UPI",
        items=[schemas.SalesItemCreate(product_id=prod.id, quantity=3)],
        idempotency_key="IDEMP-TX-UNIQUE-999",
    )

    # First transaction attempt
    tx1 = SalesService.process_checkout(
        db=db_session,
        store_id="STORE-001",
        sales_in=sale_in,
        idempotency_key="IDEMP-TX-UNIQUE-999",
    )
    assert tx1.total_revenue == 245.0 * 3
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 47

    # Duplicate transaction attempt with same idempotency key (e.g. network retry)
    tx2 = SalesService.process_checkout(
        db=db_session,
        store_id="STORE-001",
        sales_in=sale_in,
        idempotency_key="IDEMP-TX-UNIQUE-999",
    )
    assert tx2.id == tx1.id
    assert tx2.invoice_id == tx1.invoice_id

    # Stock must remain 47 (NO double deduction!)
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 47


def test_purchase_order_lifecycle_into_ledger(db_session):
    """Verifies that receiving an approved PO adds stock into the inventory ledger."""
    store = models.Store(id="STORE-001", name="Store Delhi", owner_name="Owner A", phone="111", city="Delhi")
    db_session.add(store)
    db_session.flush()

    prod = models.Product(
        store_id="STORE-001",
        sku="SNK-001",
        name="Parle-G 250g",
        category="Snacks & Biscuits",
        cost_price=20.0,
        selling_price=25.0,
        min_reorder_level=30,
        lead_time_days=2,
    )
    db_session.add(prod)
    db_session.flush()

    InventoryService.post_ledger_event(
        db=db_session,
        store_id="STORE-001",
        product_id=prod.id,
        event_type="OPENING_STOCK",
        quantity_change=10,
        unit_cost=20.0,
        reference_id="INIT-TEST",
    )
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 10

    # 1. Draft PO
    po_in = schemas.POCreate(
        supplier_name="Parle Products Mandi Depot",
        items=[schemas.POItemCreate(product_id=prod.id, quantity_ordered=50, unit_cost=20.0)],
    )
    po = PurchaseOrderService.create_po(db=db_session, store_id="STORE-001", po_in=po_in)
    assert po.status == "DRAFT"

    # 2. Approve PO
    po_approved = PurchaseOrderService.approve_po(db=db_session, store_id="STORE-001", po_id=po.id)
    assert po_approved.status == "APPROVED"

    # 3. Receive PO into stock
    po_received = PurchaseOrderService.receive_po(db=db_session, store_id="STORE-001", po_id=po.id)
    assert po_received.status == "RECEIVED"

    # Stock should now be 10 + 50 = 60
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 60


def test_daily_brief_intelligence(db_session):
    """Verifies morning intelligence brief calculations."""
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

    # Initial stock: 5 (Below min_reorder_level 20 -> will trigger reorder suggestion)
    InventoryService.post_ledger_event(
        db=db_session,
        store_id="STORE-001",
        product_id=prod.id,
        event_type="OPENING_STOCK",
        quantity_change=5,
        unit_cost=225.0,
        reference_id="INIT-TEST",
    )

    brief = IntelligenceService.get_morning_brief(db=db_session, store_id="STORE-001")
    assert brief.predicted_sales_inr > 0
    assert brief.low_stock_products_count >= 1
    assert len(brief.purchase_suggestions) >= 1
    assert brief.purchase_suggestions[0].sku == "STP-001"
