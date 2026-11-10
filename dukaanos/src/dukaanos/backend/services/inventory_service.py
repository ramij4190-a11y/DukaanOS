"""Inventory Ledger Service.

Enforces event-sourced inventory balance rules:
- No stock is ever silently updated.
- Every delta (+/-) requires an atomic InventoryLedger event.
- Point-in-time and current stock reconstruction.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dukaanos.src.dukaanos.backend import models


class InventoryService:
    """Handles all inventory ledger mutations and audits."""

    @staticmethod
    def get_current_stock(db: Session, store_id: str, product_id: int) -> int:
        """Retrieves the latest running balance for a product within the tenant store."""
        latest_entry = (
            db.query(models.InventoryLedger)
            .filter(
                models.InventoryLedger.store_id == store_id,
                models.InventoryLedger.product_id == product_id,
            )
            .order_by(desc(models.InventoryLedger.date), desc(models.InventoryLedger.id))
            .first()
        )
        return latest_entry.running_balance if latest_entry else 0

    @staticmethod
    def post_ledger_event(
        db: Session,
        store_id: str,
        product_id: int,
        event_type: str,
        quantity_change: int,
        unit_cost: float,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> models.InventoryLedger:
        """Atomically calculates new running balance and appends an immutable ledger record."""
        current_balance = InventoryService.get_current_stock(db, store_id, product_id)
        new_balance = current_balance + quantity_change

        # Generate unique transaction id
        tx_count = db.query(models.InventoryLedger).count() + 1
        tx_id = f"TX-{tx_count:07d}"

        entry = models.InventoryLedger(
            store_id=store_id,
            transaction_id=tx_id,
            date=datetime.utcnow(),
            product_id=product_id,
            event_type=event_type,
            quantity_change=quantity_change,
            running_balance=new_balance,
            unit_cost=unit_cost,
            reference_id=reference_id,
            notes=notes,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def reconcile_physical_stock(
        db: Session,
        store_id: str,
        product_id: int,
        physical_count: int,
        notes: str = "Physical stock audit",
    ) -> models.InventoryLedger:
        """Reconciles physical shop stock count against the digital ledger by posting an ADJUSTMENT event."""
        current_balance = InventoryService.get_current_stock(db, store_id, product_id)
        delta = physical_count - current_balance

        product = db.query(models.Product).filter(
            models.Product.store_id == store_id,
            models.Product.id == product_id,
        ).first()
        cost_price = product.cost_price if product else 0.0

        return InventoryService.post_ledger_event(
            db=db,
            store_id=store_id,
            product_id=product_id,
            event_type="ADJUSTMENT",
            quantity_change=delta,
            unit_cost=cost_price,
            reference_id="AUDIT-RECONCILE",
            notes=f"{notes} (Discrepancy: {delta:+d} units)",
        )

