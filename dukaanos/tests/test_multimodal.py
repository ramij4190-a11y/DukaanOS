"""Automated Test Suite for Phase 7: Multimodal Ingestion & Omnichannel WhatsApp Bridge."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dukaanos.src.dukaanos.backend.database import Base
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.main import serve_dashboard
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.multimodal.invoice_parser import (
    InvoiceParserService, InvoiceStagingResult, ParsedInvoiceItem
)
from dukaanos.src.dukaanos.multimodal.whatsapp_bridge import (
    WhatsAppBridgeService, WhatsAppOrderRequest, WhatsAppOrderItem
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


def test_clean_text_and_similarity():
    """Verifies text normalization and composite similarity scoring."""
    raw = "Aashir Atta 5kg"
    cat_name = "Aashirvaad Superior MP Atta 5kg"
    sku = "STP-001"

    score = InvoiceParserService.compute_similarity(raw, cat_name, sku)
    assert score > 0.60
    assert score <= 1.0


def test_fuzzy_catalog_matching():
    """Verifies that noisy supplier bill lines correctly match catalog SKUs."""
    catalog = [
        {"id": 1, "sku": "STP-001", "name": "Aashirvaad Superior MP Atta 5kg", "category": "Staples & Grains", "cost_price": 225.0},
        {"id": 2, "sku": "OIL-001", "name": "Fortune Sunlite Sunflower Oil 1L", "category": "Edible Oils & Ghee", "cost_price": 135.0},
        {"id": 3, "sku": "SNK-001", "name": "Parle-G Glucose Biscuits 250g", "category": "Snacks & Biscuits", "cost_price": 20.0},
    ]

    matched, score, status = InvoiceParserService.match_item_to_catalog("Fortune Sunlite 1L", catalog)
    assert matched is not None
    assert matched["sku"] == "OIL-001"
    assert status in ["AUTO_MATCHED", "PENDING_REVIEW"]


def test_parse_raw_invoice_text():
    """Verifies parsing a multi-line Mandi wholesale invoice."""
    catalog = [
        {"id": 1, "sku": "STP-001", "name": "Aashirvaad Superior MP Atta 5kg", "category": "Staples & Grains", "cost_price": 225.0},
        {"id": 2, "sku": "OIL-001", "name": "Fortune Sunlite Sunflower Oil 1L", "category": "Edible Oils & Ghee", "cost_price": 135.0},
    ]

    invoice_raw = """
    Wholesale Mandi Invoice
    Aashir Atta 5kg 20 225.00
    Fortune Sunlite Oil 1L 15 135.00
    """

    res = InvoiceParserService.parse_raw_invoice_text(invoice_raw, catalog)
    assert res.items_count == 2
    assert res.total_amount == (20 * 225.00) + (15 * 135.00)
    assert res.items[0].matched_sku == "STP-001"
    assert res.items[1].matched_sku == "OIL-001"


def test_staged_invoice_ledger_commit(db_session):
    """Verifies that committing an invoice adds stock into the inventory ledger."""
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

    # Initial stock in ledger = 10
    InventoryService.post_ledger_event(
        db=db_session,
        store_id="STORE-001",
        product_id=prod.id,
        event_type="OPENING_STOCK",
        quantity_change=10,
        unit_cost=225.0,
        reference_id="INIT-TEST",
    )
    assert InventoryService.get_current_stock(db_session, "STORE-001", prod.id) == 10

    # Create staged invoice payload with 25 incoming units
    staged = InvoiceStagingResult(
        invoice_number="INV-MANDI-999",
        supplier_name="ITC North Mandi",
        invoice_date="2026-11-10",
        total_amount=5625.0,
        items_count=1,
        auto_matched_count=1,
        review_required_count=0,
        items=[
            ParsedInvoiceItem(
                raw_text="Aashir Atta 5kg",
                extracted_qty=25,
                extracted_rate=225.0,
                matched_product_id=prod.id,
                matched_sku=prod.sku,
                matched_name=prod.name,
                confidence_score=0.95,
                status="AUTO_MATCHED",
            )
        ],
    )

    result = InvoiceParserService.commit_staged_invoice_to_ledger(
        db=db_session,
        store_id="STORE-001",
        staged_invoice=staged,
    )

    assert result["status"] == "COMMITTED_TO_LEDGER"
    assert result["total_items_posted"] == 1

    # Verified stock incremented (10 + 25 = 35)
    new_stock = InventoryService.get_current_stock(db_session, "STORE-001", prod.id)
    assert new_stock == 35


def test_whatsapp_po_formatting_multilingual():
    """Verifies localized WhatsApp procurement message formatting in Hindi, Hinglish, and English."""
    req = WhatsAppOrderRequest(
        store_name="Shree Ganesh Kirana",
        supplier_phone="919876543210",
        supplier_name="Mandi Wholesaler",
        language="hinglish",
        items=[
            WhatsAppOrderItem(name="Aashirvaad Atta 5kg", quantity=20, unit="bags"),
            WhatsAppOrderItem(name="Fortune Sunflower Oil 1L", quantity=15, unit="bottles"),
        ],
    )

    res_hinglish = WhatsAppBridgeService.generate_whatsapp_link(req)
    assert "https://wa.me/919876543210?text=" in res_hinglish["whatsapp_url"]
    assert "Aashirvaad Atta 5kg" in res_hinglish["raw_message"]

    # Test Hindi template
    req.language = "hindi"
    res_hindi = WhatsAppBridgeService.generate_whatsapp_link(req)
    assert "नमस्ते भाईजी" in res_hindi["raw_message"]

    # Test English template
    req.language = "english"
    res_english = WhatsAppBridgeService.generate_whatsapp_link(req)
    assert "DUKAANOS PURCHASE ORDER" in res_english["raw_message"]


def test_frontend_html_serving():
    """Verifies that the dashboard HTML endpoint responds with HTTP 200 and UI content."""
    res = serve_dashboard()
    assert res.status_code == 200
    assert "DukaanOS" in res.body.decode("utf-8")
