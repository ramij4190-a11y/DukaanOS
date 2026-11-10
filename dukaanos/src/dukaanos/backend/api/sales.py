"""Sales & Checkout Counter Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.api.deps import get_current_user
from dukaanos.src.dukaanos.backend.services.sales_service import SalesService

router = APIRouter(prefix="/sales", tags=["Sales & POS Checkout"])


@router.post("", response_model=schemas.SalesOut)
def create_sales_checkout(
    sales_in: schemas.SalesCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Processes counter basket checkout with atomic ledger deduction and idempotency key protection."""
    key = idempotency_key or sales_in.idempotency_key
    tx = SalesService.process_checkout(
        db=db,
        store_id=current_user.store_id,
        sales_in=sales_in,
        idempotency_key=key,
    )
    return tx


@router.get("", response_model=List[schemas.SalesOut])
def list_sales_transactions(
    limit: int = Query(25, le=200),
    offset: int = Query(0, ge=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists recent sales transactions for the store."""
    transactions = (
        db.query(models.SalesTransaction)
        .filter(models.SalesTransaction.store_id == current_user.store_id)
        .order_by(desc(models.SalesTransaction.date))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return transactions

