"""Purchase Orders & Procurement Lifecycle API."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.api.deps import get_current_user
from dukaanos.src.dukaanos.backend.services.po_service import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders & Procurement"])


@router.get("", response_model=List[schemas.POOut])
def list_purchase_orders(
    status: str = Query(None),
    limit: int = Query(25, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists purchase orders for the store."""
    query = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.store_id == current_user.store_id
    )
    if status:
        query = query.filter(models.PurchaseOrder.status == status.upper())

    return query.order_by(desc(models.PurchaseOrder.order_date)).limit(limit).all()


@router.post("", response_model=schemas.POOut)
def draft_purchase_order(
    po_in: schemas.POCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Drafts a new purchase order for supplier procurement."""
    return PurchaseOrderService.create_po(db=db, store_id=current_user.store_id, po_in=po_in)


@router.post("/{po_id}/approve", response_model=schemas.POOut)
def approve_purchase_order(
    po_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Human-in-the-loop owner approval: commits draft PO into approved status."""
    return PurchaseOrderService.approve_po(db=db, store_id=current_user.store_id, po_id=po_id)


@router.post("/{po_id}/receive", response_model=schemas.POOut)
def receive_goods_into_ledger(
    po_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receives supplier stock arrival, automatically updating the store's inventory ledger."""
    return PurchaseOrderService.receive_po(db=db, store_id=current_user.store_id, po_id=po_id)

