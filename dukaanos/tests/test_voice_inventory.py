"""Automated Test Suite for Voice AI Inventory Management Engine."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dukaanos.src.dukaanos.backend.database import Base
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.voice_enterprise.voice_inventory import (
    VoiceInventoryAI, VoiceInventoryRequest
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


@pytest.fixture
def store_and_catalog(db_session):
    """Sets up store tenant and catalog products."""
    store = models.Store(id="STORE-001", name="Store Delhi", owner_name="Owner A", phone="111", city="Delhi")
    db_session.add(store)
    db_session.flush()

    prod1 = models.Product(
        store_id="STORE-001", sku="STP-001", name="Aashirvaad Shudh Chakki Atta 5kg",
        category="Staples & Grains", cost_price=225.0, selling_price=245.0,
        min_reorder_level=20, lead_time_days=2,
    )
    prod2 = models.Product(
        store_id="STORE-001", sku="OIL-002", name="Dhara Kachi Ghani Mustard Oil 1L",
        category="Edible Oils & Ghee", cost_price=142.0, selling_price=165.0,
        min_reorder_level=20, lead_time_days=2,
    )
    prod3 = models.Product(
        store_id="STORE-001", sku="PCK-004", name="Parle-G Glucose Biscuits 250g",
        category="Snacks & Biscuits", cost_price=20.0, selling_price=25.0,
        min_reorder_level=30, lead_time_days=2,
    )
    db_session.add_all([prod1, prod2, prod3])
    db_session.flush()

    # Initial stocks in ledger: Atta=50, Oil=30, Parle-G=80
    InventoryService.post_ledger_event(db_session, "STORE-001", prod1.id, "OPENING_STOCK", 50, 225.0, "INIT")
    InventoryService.post_ledger_event(db_session, "STORE-001", prod2.id, "OPENING_STOCK", 30, 142.0, "INIT")
    InventoryService.post_ledger_event(db_session, "STORE-001", prod3.id, "OPENING_STOCK", 80, 20.0, "INIT")

    catalog = [
        {"id": prod1.id, "sku": prod1.sku, "name": prod1.name, "cost_price": prod1.cost_price, "selling_price": prod1.selling_price},
        {"id": prod2.id, "sku": prod2.sku, "name": prod2.name, "cost_price": prod2.cost_price, "selling_price": prod2.selling_price},
        {"id": prod3.id, "sku": prod3.sku, "name": prod3.name, "cost_price": prod3.cost_price, "selling_price": prod3.selling_price},
    ]
    return store, catalog


def test_voice_stock_inward_addition(db_session, store_and_catalog):
    """Verifies that saying 'Aashirvaad Atta 20 packet naya aaya hai add karo' adds 20 units."""
    store, catalog = store_and_catalog
    spoken = "Aashirvaad Atta 20 packet naya aaya hai add karo"

    result = VoiceInventoryAI.process_voice_inventory_update(
        db=db_session,
        store_id="STORE-001",
        spoken_text=spoken,
        catalog=catalog,
    )

    assert result.success is True
    assert result.event_type == "PURCHASE"
    assert result.sku == "STP-001"
    assert result.quantity_delta == 20
    assert result.previous_stock == 50
    assert result.new_running_stock == 70  # 50 + 20 = 70
    assert "add ho gaye" in result.voice_reply_text

    # Verify directly from ledger
    assert InventoryService.get_current_stock(db_session, "STORE-001", result.product_id) == 70


def test_voice_damage_wastage_deduction(db_session, store_and_catalog):
    """Verifies that saying 'Dhara tel paanch bottle kharab ho gaya nikal do' deducts 5 units."""
    store, catalog = store_and_catalog
    spoken = "Dhara tel paanch bottle kharab ho gaya nikal do"

    result = VoiceInventoryAI.process_voice_inventory_update(
        db=db_session,
        store_id="STORE-001",
        spoken_text=spoken,
        catalog=catalog,
    )

    assert result.success is True
    assert result.event_type == "DAMAGE_EXPIRED"
    assert result.sku == "OIL-002"
    assert result.quantity_delta == -5
    assert result.previous_stock == 30
    assert result.new_running_stock == 25  # 30 - 5 = 25
    assert "damaged units nikal diye" in result.voice_reply_text


def test_voice_stock_audit_reconciliation(db_session, store_and_catalog):
    """Verifies that saying 'Parle-G ka stock ginti kiya 50 bacha hai' reconciles target count to 50."""
    store, catalog = store_and_catalog
    spoken = "Parle-G ka stock ginti kiya 50 bacha hai"

    result = VoiceInventoryAI.process_voice_inventory_update(
        db=db_session,
        store_id="STORE-001",
        spoken_text=spoken,
        catalog=catalog,
    )

    assert result.success is True
    assert result.event_type == "ADJUSTMENT"
    assert result.sku == "PCK-004"
    assert result.previous_stock == 80
    assert result.quantity_delta == -30  # Delta from 80 -> 50
    assert result.new_running_stock == 50
    assert "reconcile ho gaya" in result.voice_reply_text


def test_voice_multilingual_language_detection():
    """Verifies intent and language detection across Hindi, Bengali, Gujarati, and English."""
    # Bengali
    lang_bn, intent_bn, event_bn = VoiceInventoryAI.detect_intent_and_event("Atta notun esheche 10 bori stock-e dhukao")
    assert lang_bn == "Bengali"
    assert event_bn == "PURCHASE"

    # Gujarati
    lang_gu, intent_gu, event_gu = VoiceInventoryAI.detect_intent_and_event("Tel kharab thayi gayu 2 bottle")
    assert lang_gu == "Gujarati"
    assert event_gu == "DAMAGE_EXPIRED"

    # English
    lang_en, intent_en, event_en = VoiceInventoryAI.detect_intent_and_event("physical count is 40 units")
    assert lang_en == "English"
    assert event_en == "ADJUSTMENT"

