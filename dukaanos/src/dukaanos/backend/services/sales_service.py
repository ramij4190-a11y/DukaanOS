"""Sales Transaction and Counter Checkout Service.

Implements:
- Challenge 03: Idempotency Protection against duplicate billing/double-charging
- Atomic inventory ledger deduction
- Margin and basket gross profit computation
"""

from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService


class SalesService:
    """Manages checkout basket transactions and ledger updates."""

    @staticmethod
    def process_checkout(
        db: Session,
        store_id: str,
        sales_in: schemas.SalesCreate,
        idempotency_key: Optional[str] = None,
    ) -> models.SalesTransaction:
        """Processes counter checkout transaction with idempotency and atomic ledger deduction."""
        # 1. Challenge 03: Idempotency Key check
        key = idempotency_key or sales_in.idempotency_key
        if key:
            existing = (
                db.query(models.SalesTransaction)
                .filter(
                    models.SalesTransaction.store_id == store_id,
                    models.SalesTransaction.idempotency_key == key,
                )
                .first()
            )
            if existing:
                # Return previously processed transaction safely without re-deducting stock
                return existing

        # 2. Validate items and verify current stock
        line_items_data = []
        total_revenue = 0.0
        total_cost = 0.0

        for item in sales_in.items:
            product = (
                db.query(models.Product)
                .filter(
                    models.Product.store_id == store_id,
                    models.Product.id == item.product_id,
                    models.Product.is_active.is_(True),
                )
                .first()
            )
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product ID {item.product_id} not found in this store.",
                )

            # Check stock
            avail_stock = InventoryService.get_current_stock(db, store_id, product.id)
            if avail_stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient inventory for '{product.name}'. Available: {avail_stock}, Requested: {item.quantity}",
                )

            line_revenue = round(item.quantity * product.selling_price, 2)
            line_cost = round(item.quantity * product.cost_price, 2)
            total_revenue += line_revenue
            total_cost += line_cost

            line_items_data.append({
                "product": product,
                "quantity": item.quantity,
                "unit_price": product.selling_price,
                "cost_price": product.cost_price,
                "line_total": line_revenue,
            })

        gross_profit = round(total_revenue - total_cost, 2)

        # 3. Generate unique invoice number
        count = db.query(models.SalesTransaction).filter(models.SalesTransaction.store_id == store_id).count() + 1001
        invoice_id = f"INV-{count}"

        # 4. Save Sales Header
        tx = models.SalesTransaction(
            store_id=store_id,
            invoice_id=invoice_id,
            idempotency_key=key,
            date=datetime.utcnow(),
            payment_method=sales_in.payment_method.upper(),
            total_revenue=total_revenue,
            total_cost=total_cost,
            gross_profit=gross_profit,
        )
        db.add(tx)
        db.flush()  # Obtain tx.id

        # 5. Save Line Items & Deduct from Inventory Ledger
        for item_info in line_items_data:
            line = models.SalesItem(
                transaction_id=tx.id,
                product_id=item_info["product"].id,
                quantity=item_info["quantity"],
                unit_price=item_info["unit_price"],
                cost_price=item_info["cost_price"],
                line_total=item_info["line_total"],
            )
            db.add(line)

            # Post ledger deduction event
            InventoryService.post_ledger_event(
                db=db,
                store_id=store_id,
                product_id=item_info["product"].id,
                event_type="SALE",
                quantity_change=-item_info["quantity"],
                unit_cost=item_info["cost_price"],
                reference_id=invoice_id,
                notes=f"Customer counter sale ({sales_in.payment_method})",
            )

        db.commit()
        db.refresh(tx)
        return tx

