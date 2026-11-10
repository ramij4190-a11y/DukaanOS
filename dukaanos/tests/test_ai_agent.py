"""Automated Test Suite for Phase 4 AI Retail Agent."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dukaanos.src.dukaanos.backend.database import Base
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.ai.agent.engine import RetailAgentEngine
from dukaanos.src.dukaanos.ai.agent.schema import ChatRequest
from dukaanos.src.dukaanos.ai.agent.guardrails import AgentGuardrails

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_ai_db():
    """Sets up an in-memory database with test store and products."""
    Base.metadata.create_all(bind=engine)
    db = TestSession()

    store = models.Store(id="TEST-STORE", name="Test Kirana", owner_name="Owner", phone="9999999999")
    db.add(store)
    db.flush()

    p1 = models.Product(
        store_id="TEST-STORE",
        sku="STP-001",
        name="Aashirvaad Shudh Chakki Atta 5kg",
        category="Staples & Grains",
        unit="Bag",
        cost_price=225.0,
        selling_price=245.0,
        min_reorder_level=20,
        lead_time_days=2,
        supplier_name="Shree Ganesh Mandi",
        is_active=True,
    )
    p2 = models.Product(
        store_id="TEST-STORE",
        sku="PCK-001",
        name="Maggi 2-Minute Noodles 70g",
        category="Packaged Foods & Snacks",
        unit="Pouch",
        cost_price=11.5,
        selling_price=14.0,
        min_reorder_level=40,
        lead_time_days=1,
        supplier_name="MahaLaxmi FMCG",
        is_active=True,
    )
    db.add_all([p1, p2])
    db.commit()

    # Initial stock: Atta has 10 units (LOW STOCK < 20), Maggi has 80 units (HEALTHY > 40)
    InventoryService.post_ledger_event(db, "TEST-STORE", p1.id, "OPENING_STOCK", 10, 225.0, "INIT")
    InventoryService.post_ledger_event(db, "TEST-STORE", p2.id, "OPENING_STOCK", 80, 11.5, "INIT")

    yield db, "TEST-STORE"
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_stock_inquiry_intent_and_tool(setup_ai_db):
    """Verifies that asking about stock in Hinglish executes get_inventory_status."""
    db, store_id = setup_ai_db
    agent = RetailAgentEngine(store_id=store_id, db=db)

    req = ChatRequest(message="Atta ka stock kitna hai?")
    resp = agent.process_message(req)

    assert "get_inventory_status" in resp.tools_executed
    assert "Aashirvaad" in resp.reply_text
    assert "10" in resp.reply_text  # Exact ledger stock
    assert resp.data_snapshot["stock_health"] == "LOW_STOCK"


def test_reorder_intent_and_proposal(setup_ai_db):
    """Verifies that reorder inquiries propose a draft PO requiring human confirmation."""
    db, store_id = setup_ai_db
    agent = RetailAgentEngine(store_id=store_id, db=db)

    req = ChatRequest(message="Which products should I order tomorrow?")
    resp = agent.process_message(req)

    assert "calculate_reorder_quantities" in resp.tools_executed
    assert resp.proposed_action is not None
    assert resp.proposed_action.action_type == "CREATE_PURCHASE_ORDER"
    assert resp.proposed_action.requires_human_approval is True
    assert resp.proposed_action.estimated_amount_inr > 0


def test_demand_forecasting_intent(setup_ai_db):
    """Verifies demand forecasting tool invocation."""
    db, store_id = setup_ai_db
    agent = RetailAgentEngine(store_id=store_id, db=db)

    req = ChatRequest(message="Show 7-day demand forecast for Maggi")
    resp = agent.process_message(req)

    assert "get_product_forecast" in resp.tools_executed
    assert "Demand Forecast" in resp.reply_text
    assert resp.data_snapshot["forecasted_demand_units"] > 0


def test_guardrail_budget_rejection():
    """Verifies that excessive order drafts (> ₹1.5 Lakhs) get rejected by safety guardrails."""
    unsafe_proposal = {
        "supplier_name": "Big Distributor",
        "total_order_amount_inr": 250000.0,  # Exceeds 1.5 Lakhs cap
        "items": [{"product_id": 1, "name": "Bulk Sugar", "quantity": 100}],
    }
    is_valid, reason = AgentGuardrails.validate_purchase_order(unsafe_proposal)
    assert is_valid is False
    assert "budget cap" in reason


def test_action_confirmation_and_execution(setup_ai_db):
    """Verifies that confirming a proposed draft PO creates and approves an order in the database."""
    db, store_id = setup_ai_db
    agent = RetailAgentEngine(store_id=store_id, db=db)

    p1 = db.query(models.Product).filter(models.Product.store_id == store_id).first()
    proposal_payload = {
        "supplier_name": "Shree Ganesh Mandi",
        "items": [{"product_id": p1.id, "quantity": 15, "unit_cost": p1.cost_price}],
    }

    result = agent.execute_confirmed_action(action_type="CREATE_PURCHASE_ORDER", payload=proposal_payload)
    assert result["status"] == "success"
    assert "po_number" in result

    # Verify PO in database
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.po_number == result["po_number"]).first()
    assert po is not None
    assert po.status == "APPROVED"
    assert po.total_amount == 15 * p1.cost_price

