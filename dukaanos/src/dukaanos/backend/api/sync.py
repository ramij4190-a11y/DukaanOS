"""Edge Sync API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.edge.sync_service import (
    EdgeSyncService, BatchSyncRequest, BatchSyncResponse
)

router = APIRouter(prefix="/sync", tags=["Offline-First Edge Sync"])


@router.post("/batch", response_model=BatchSyncResponse)
def sync_offline_transactions(
    batch: BatchSyncRequest,
    db: Session = Depends(get_db),
):
    """Reconciles an offline queue batch with strict idempotency deduplication."""
    return EdgeSyncService.reconcile_batch(db=db, batch=batch)

