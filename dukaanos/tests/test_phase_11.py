"""Test suite for Phase 11: Autonomous Self-Learning Store Brain."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dukaanos.src.dukaanos.backend.models import Base, Store, Product
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.brain.autonomous_brain import AutonomousStoreBrain
from dukaanos.src.dukaanos.voice_enterprise.voice_inventory import VoiceInventoryAI


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    store = Store(id="STORE-001", name="Shree Ganesh Kirana", owner_name="Ramesh Kumar", phone="9876543210")
    db.add(store)
    db.commit()

    prod = Product(
        id=1,
        store_id="STORE-001",
        sku="STP-001",
        name="Aashirvaad Shudh Chakki Atta 5kg",
        category="Staples",
        cost_price=225.0,
        selling_price=260.0
    )
    db.add(prod)
    db.commit()

    InventoryService.post_ledger_event(
        db=db,
        store_id="STORE-001",
        product_id=1,
        event_type="OPENING",
        quantity_change=50,
        unit_cost=225.0,
        notes="Opening balance"
    )

    yield db
    db.close()


def test_online_learning_velocity_update():
    """Verifies that sales transactions incrementally update EWMA velocity and volatility."""
    brain = AutonomousStoreBrain(store_id="TEST-STORE-001")
    p = brain.profiles["STP-001"]
    initial_vel = p.learned_daily_velocity

    # Ingest 3 consecutive high-volume sales signals (e.g. 15 units sold)
    for _ in range(3):
        brain.ingest_signal(
            sku="STP-001",
            product_name="Aashirvaad Shudh Chakki Atta 5kg",
            event_type="SALE",
            quantity_delta=-15,
            new_balance=35,
            unit_cost=225.0,
            selling_price=260.0
        )

    # Learned velocity must adapt upwards
    assert p.learned_daily_velocity > initial_vel
    assert p.total_events_observed > 1
    assert p.dynamic_reorder_point > 0


def test_autonomous_stockout_po_drafting():
    """Verifies that stock depletion triggers an auto-drafted Restock PO."""
    brain = AutonomousStoreBrain(store_id="TEST-STORE-002")
    
    # Ingest critical depletion signal: stock drops to 4 units
    brain.ingest_signal(
        sku="STP-001",
        product_name="Aashirvaad Shudh Chakki Atta 5kg",
        event_type="SALE",
        quantity_delta=-46,
        new_balance=4,
        unit_cost=225.0,
        selling_price=260.0
    )

    p = brain.profiles["STP-001"]
    assert p.status in ["CRITICAL_DEPLETION", "REORDER_NEEDED"]
    assert p.days_to_depletion < 3.0

    # Auto-drafted action must be created
    po_actions = [a for a in brain.actions if a.product_sku == "STP-001" and a.action_type == "AUTO_RESTOCK_PO"]
    assert len(po_actions) >= 1
    action = po_actions[0]
    assert action.urgency == "CRITICAL"
    assert action.recommended_payload["suggested_qty"] > 0
    assert not action.auto_executed

    # Execute action
    executed = brain.execute_action(action.action_id)
    assert executed is True
    assert action.auto_executed is True


def test_dead_capital_overstock_markdown():
    """Verifies that overstocked dead capital triggers a clearance markdown recommendation."""
    brain = AutonomousStoreBrain(store_id="TEST-STORE-003")

    # Ingest massive overstock (e.g. 150 units of Tata Tea Gold with low 2.0 velocity)
    brain.ingest_signal(
        sku="PCK-019",
        product_name="Tata Tea Gold 500g",
        event_type="PURCHASE",
        quantity_delta=+125,
        new_balance=150,
        unit_cost=220.0,
        selling_price=260.0
    )

    p = brain.profiles["PCK-019"]
    assert p.status == "OVERSTOCKED"
    assert p.days_to_depletion > 25.0

    markdown_actions = [a for a in brain.actions if a.product_sku == "PCK-019" and a.action_type == "EXPIRY_MARKDOWN"]
    assert len(markdown_actions) >= 1
    assert "Dead Capital" in markdown_actions[0].title


def test_voice_inventory_autonomous_brain_loop(test_db):
    """Verifies that spoken vernacular voice commands directly feed into the Autonomous Brain."""
    catalog = [{
        "id": 1,
        "sku": "STP-001",
        "name": "Aashirvaad Shudh Chakki Atta 5kg",
        "category": "Staples",
        "cost_price": 225.0,
        "selling_price": 260.0
    }]

    # Shopkeeper speaks an inward addition of 20 packets
    res = VoiceInventoryAI.process_voice_inventory_update(
        db=test_db,
        store_id="STORE-001",
        spoken_text="Aashirvaad Atta 20 packet naya aaya",
        catalog=catalog
    )

    assert res.success is True
    assert res.quantity_delta == 20
    assert res.new_running_stock == 70
    assert res.days_to_depletion is not None
    assert res.brain_status in ["HEALTHY", "REORDER_NEEDED", "OVERSTOCKED"]
