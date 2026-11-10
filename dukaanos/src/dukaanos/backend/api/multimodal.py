"""Multimodal & Omnichannel API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.multimodal.invoice_parser import (
    InvoiceParserService, InvoiceStagingResult
)
from dukaanos.src.dukaanos.multimodal.whatsapp_bridge import (
    WhatsAppBridgeService, WhatsAppOrderRequest
)

router = APIRouter(prefix="/multimodal", tags=["Multimodal & Omnichannel"])


class InvoiceTextParseRequest(BaseModel):
    store_id: str = "STORE-001"
    supplier_name: str = "Wholesale Mandi Depot"
    invoice_raw_text: str


@router.post("/invoice/parse", response_model=InvoiceStagingResult)
def parse_raw_invoice(
    payload: InvoiceTextParseRequest,
    db: Session = Depends(get_db),
):
    """Parses raw invoice text from paper receipts/OCR and performs fuzzy catalog matching."""
    # Fetch active products for the store
    products = db.query(models.Product).filter(
        models.Product.store_id == payload.store_id,
        models.Product.is_active.is_(True),
    ).all()

    catalog = [
        {"id": p.id, "sku": p.sku, "name": p.name, "category": p.category, "cost_price": p.cost_price}
        for p in products
    ]

    return InvoiceParserService.parse_raw_invoice_text(
        invoice_text=payload.invoice_raw_text,
        catalog=catalog,
        default_supplier=payload.supplier_name,
    )


@router.post("/invoice/confirm")
def confirm_and_commit_invoice(
    staged_invoice: InvoiceStagingResult,
    store_id: str = "STORE-001",
    db: Session = Depends(get_db),
):
    """Owner confirmation gate: Atomically commits confirmed invoice items into the inventory ledger."""
    return InvoiceParserService.commit_staged_invoice_to_ledger(
        db=db,
        store_id=store_id,
        staged_invoice=staged_invoice,
    )


@router.post("/whatsapp/generate-order")
def generate_whatsapp_order_link(req: WhatsAppOrderRequest):
    """Generates direct wa.me link with localized procurement message."""
    return WhatsAppBridgeService.generate_whatsapp_link(req)


@router.post("/whatsapp/webhook")
def simulate_whatsapp_webhook(
    sender: str = Body(..., embed=True),
    message: str = Body(..., embed=True),
):
    """Simulates inbound WhatsApp webhook message parsing."""
    return WhatsAppBridgeService.parse_inbound_whatsapp_message(sender_phone=sender, message_body=message)

