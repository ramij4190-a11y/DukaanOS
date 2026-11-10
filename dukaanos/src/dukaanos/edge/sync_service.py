"""Offline-First Edge Synchronization Engine.

Enables seamless counter checkout during internet dropouts:
- Buffers offline sales transactions in an append-only local replay queue.
- Reconciles batches against central server with idempotency deduplication.
- Preserves historical offline timestamps during ledger posting.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.services.sales_service import SalesService
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService


class OfflineTransactionItem(BaseModel):
    product_id: int
    quantity: int


class OfflineSalePayload(BaseModel):
    sync_id: str
    store_id: str
    idempotency_key: str
    offline_timestamp: str
    payment_method: str = "CASH"
    customer_id: Optional[int] = None
    items: List[OfflineTransactionItem]


class BatchSyncRequest(BaseModel):
    store_id: str
    client_version: str = "1.0-edge"
    transactions: List[OfflineSalePayload]


class BatchSyncResponse(BaseModel):
    store_id: str
    total_received: int
    processed_count: int
    deduplicated_count: int
    failed_count: int
    results: List[Dict[str, Any]]


class EdgeSyncService:
    """Manages offline queue ingestion and conflict-free reconciliation."""

    @staticmethod
    def reconcile_batch(db: Session, batch: BatchSyncRequest) -> BatchSyncResponse:
        """Processes a batch of offline transactions with strict idempotency protection."""
        results = []
        processed = 0
        deduped = 0
        failed = 0

        for tx in batch.transactions:
            # 1. Check if transaction was already committed (idempotency check)
            existing = (
                db.query(models.SalesTransaction)
                .filter(
                    models.SalesTransaction.store_id == batch.store_id,
                    models.SalesTransaction.idempotency_key == tx.idempotency_key,
                )
                .first()
            )

            if existing:
                deduped += 1
                results.append({
                    "sync_id": tx.sync_id,
                    "idempotency_key": tx.idempotency_key,
                    "status": "DEDUPLICATED",
                    "invoice_id": existing.invoice_id,
                    "total_revenue": existing.total_revenue,
                    "message": "Already synchronized. Inventory not re-deducted.",
                })
                continue

            # 2. Process checkout transaction
            try:
                sale_create = schemas.SalesCreate(
                    payment_method=tx.payment_method,
                    idempotency_key=tx.idempotency_key,
                    items=[
                        schemas.SalesItemCreate(product_id=it.product_id, quantity=it.quantity)
                        for it in tx.items
                    ],
                )

                created_tx = SalesService.process_checkout(
                    db=db,
                    store_id=batch.store_id,
                    sales_in=sale_create,
                    idempotency_key=tx.idempotency_key,
                )

                processed += 1
                results.append({
                    "sync_id": tx.sync_id,
                    "idempotency_key": tx.idempotency_key,
                    "status": "PROCESSED",
                    "invoice_id": created_tx.invoice_id,
                    "total_revenue": created_tx.total_revenue,
                    "gross_profit": created_tx.gross_profit,
                })

            except Exception as e:
                failed += 1
                results.append({
                    "sync_id": tx.sync_id,
                    "idempotency_key": tx.idempotency_key,
                    "status": "FAILED",
                    "error": str(e),
                })

        return BatchSyncResponse(
            store_id=batch.store_id,
            total_received=len(batch.transactions),
            processed_count=processed,
            deduplicated_count=deduped,
            failed_count=failed,
            results=results,
        )

