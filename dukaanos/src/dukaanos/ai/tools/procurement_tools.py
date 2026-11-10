"""Procurement and Reordering Tools for the AI Agent."""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService


def calculate_reorder_quantities(store_id: str, db: Session) -> Dict[str, Any]:
    """Calculates suggested replenishment quantities for depleted products based on lead times and ROP."""
    products = (
        db.query(models.Product)
        .filter(models.Product.store_id == store_id, models.Product.is_active.is_(True))
        .all()
    )

    reorder_list = []
    total_cost_estimate = 0.0

    for prod in products:
        current_stock = InventoryService.get_current_stock(db, store_id, prod.id)
        if current_stock <= prod.min_reorder_level:
            daily_vel = max(2.0, prod.min_reorder_level / 4.0)
            # Reorder for 7-10 days review cycle
            suggested_qty = max(int(daily_vel * 8.0), 10)
            cost = round(suggested_qty * prod.cost_price, 2)
            total_cost_estimate += cost

            reorder_list.append({
                "product_id": prod.id,
                "sku": prod.sku,
                "name": prod.name,
                "category": prod.category,
                "supplier_name": prod.supplier_name,
                "current_stock": current_stock,
                "reorder_point": prod.min_reorder_level,
                "suggested_order_qty": suggested_qty,
                "unit_cost": prod.cost_price,
                "estimated_line_cost": cost,
            })

    return {
        "status": "success",
        "items_needing_reorder_count": len(reorder_list),
        "total_estimated_purchase_cost_inr": round(total_cost_estimate, 2),
        "reorder_suggestions": reorder_list[:10],
    }


def draft_purchase_order_proposal(
    store_id: str, supplier_name: str, items: List[Dict[str, Any]], db: Session
) -> Dict[str, Any]:
    """Prepares a proposed Purchase Order draft payload for human approval (does NOT commit directly to ledger)."""
    verified_items = []
    total_amount = 0.0

    for it in items:
        prod_id = it.get("product_id")
        qty = it.get("quantity")
        prod = db.query(models.Product).filter(
            models.Product.store_id == store_id,
            models.Product.id == prod_id,
        ).first()

        if not prod:
            continue

        unit_cost = prod.cost_price
        line_total = round(qty * unit_cost, 2)
        total_amount += line_total

        verified_items.append({
            "product_id": prod.id,
            "sku": prod.sku,
            "name": prod.name,
            "quantity": qty,
            "unit_cost": unit_cost,
            "line_total": line_total,
        })

    return {
        "status": "proposal_ready",
        "action_type": "CREATE_PURCHASE_ORDER",
        "supplier_name": supplier_name,
        "items": verified_items,
        "total_order_amount_inr": round(total_amount, 2),
        "requires_human_approval": True,
        "message": f"Prepared purchase order draft of ₹{total_amount:,.2f} for '{supplier_name}' ({len(verified_items)} items). Please confirm to submit.",
    }

