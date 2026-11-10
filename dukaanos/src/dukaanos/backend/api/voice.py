"""Voice AI Inventory API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.voice_enterprise.voice_inventory import (
    VoiceInventoryAI, VoiceInventoryRequest, VoiceInventoryMutationResult
)

router = APIRouter(prefix="/voice", tags=["Voice AI Inventory"])


@router.post("/inventory-update", response_model=VoiceInventoryMutationResult)
def voice_inventory_update(
    req: VoiceInventoryRequest,
    db: Session = Depends(get_db),
):
    """Processes spoken vernacular instruction and atomically mutates the inventory ledger."""
    # Load store catalog
    products = db.query(models.Product).filter(
        models.Product.store_id == req.store_id,
        models.Product.is_active.is_(True),
    ).all()

    catalog = [
        {
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "category": p.category,
            "cost_price": p.cost_price,
            "selling_price": p.selling_price,
        }
        for p in products
    ]

    return VoiceInventoryAI.process_voice_inventory_update(
        db=db,
        store_id=req.store_id,
        spoken_text=req.spoken_text,
        catalog=catalog,
    )
