"""Inventory Ledger & Physical Stock Audit Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.api.deps import get_current_user
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory Ledger"])


@router.get("/ledger", response_model=List[schemas.LedgerEntryOut])
def get_inventory_ledger(
    product_id: Optional[int] = None,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves the complete immutable audit trail of inventory movements for the store."""
    query = db.query(models.InventoryLedger).filter(
        models.InventoryLedger.store_id == current_user.store_id
    )
    if product_id:
        query = query.filter(models.InventoryLedger.product_id == product_id)

    entries = (
        query.order_by(desc(models.InventoryLedger.date), desc(models.InventoryLedger.id))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return entries


@router.post("/reconcile", response_model=schemas.ReconciliationOut)
def reconcile_physical_stock(
    req: schemas.ReconciliationRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Audits and adjusts digital ledger balance to match verified physical counter stock."""
    product = db.query(models.Product).filter(
        models.Product.store_id == current_user.store_id,
        models.Product.id == req.product_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in this store")

    prev_stock = InventoryService.get_current_stock(db, current_user.store_id, req.product_id)
    entry = InventoryService.reconcile_physical_stock(
        db=db,
        store_id=current_user.store_id,
        product_id=req.product_id,
        physical_count=req.physical_count,
        notes=req.notes or "Counter audit",
    )

    return schemas.ReconciliationOut(
        product_id=req.product_id,
        previous_ledger_stock=prev_stock,
        physical_count=req.physical_count,
        adjustment_applied=entry.quantity_change,
        transaction_id=entry.transaction_id,
        reconciled_at=entry.date,
    )

