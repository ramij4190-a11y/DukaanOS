"""Purchase Order and Procurement Lifecycle Service."""

from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService


class PurchaseOrderService:
    """Manages purchase order drafting, approvals, and receiving into ledger."""

    @staticmethod
    def create_po(db: Session, store_id: str, po_in: schemas.POCreate) -> models.PurchaseOrder:
        """Creates a purchase order in DRAFT status."""
        count = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.store_id == store_id).count() + 101
        po_number = f"PO-{count:06d}"

        total_amount = sum(item.quantity_ordered * item.unit_cost for item in po_in.items)

        po = models.PurchaseOrder(
            store_id=store_id,
            po_number=po_number,
            supplier_name=po_in.supplier_name,
            order_date=datetime.utcnow(),
            expected_delivery_date=po_in.expected_delivery_date,
            status="DRAFT",
            total_amount=round(total_amount, 2),
        )
        db.add(po)
        db.flush()

        for item in po_in.items:
            po_item = models.PurchaseOrderItem(
                po_id=po.id,
                product_id=item.product_id,
                quantity_ordered=item.quantity_ordered,
                unit_cost=item.unit_cost,
                total_cost=round(item.quantity_ordered * item.unit_cost, 2),
            )
            db.add(po_item)

        db.commit()
        db.refresh(po)
        return po

    @staticmethod
    def approve_po(db: Session, store_id: str, po_id: int) -> models.PurchaseOrder:
        """Owner approval step: transitions PO from DRAFT to APPROVED."""
        po = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.store_id == store_id,
            models.PurchaseOrder.id == po_id,
        ).first()

        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        if po.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot approve PO in '{po.status}' status")

        po.status = "APPROVED"
        db.commit()
        db.refresh(po)
        return po

    @staticmethod
    def receive_po(db: Session, store_id: str, po_id: int) -> models.PurchaseOrder:
        """Receiving goods from supplier: marks PO as RECEIVED and posts to inventory ledger."""
        po = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.store_id == store_id,
            models.PurchaseOrder.id == po_id,
        ).first()

        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        if po.status != "APPROVED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only APPROVED POs can be received (Current: {po.status})")

        po.status = "RECEIVED"
        po.received_date = datetime.utcnow()

        # Append purchase receipt to ledger for every product
        for item in po.items:
            InventoryService.post_ledger_event(
                db=db,
                store_id=store_id,
                product_id=item.product_id,
                event_type="PURCHASE",
                quantity_change=item.quantity_ordered,
                unit_cost=item.unit_cost,
                reference_id=po.po_number,
                notes=f"Stock received from {po.supplier_name}",
            )

        db.commit()
        db.refresh(po)
        return po

