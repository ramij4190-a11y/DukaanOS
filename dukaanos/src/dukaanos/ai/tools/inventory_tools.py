"""Inventory Inspection Tools for the AI Agent."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService


def get_inventory_status(store_id: str, query: str, db: Session) -> Dict[str, Any]:
    """Retrieves real-time inventory ledger balance and pricing for a product by SKU or name."""
    search = f"%{query}%"
    product = (
        db.query(models.Product)
        .filter(
            models.Product.store_id == store_id,
            or_(models.Product.sku.ilike(search), models.Product.name.ilike(search)),
        )
        .first()
    )

    if not product:
        return {"status": "not_found", "message": f"No product matching '{query}' found in your store catalog."}

    current_stock = InventoryService.get_current_stock(db, store_id, product.id)
    rop = product.min_reorder_level

    if current_stock == 0:
        health = "OUT_OF_STOCK"
    elif current_stock <= rop:
        health = "LOW_STOCK"
    else:
        health = "HEALTHY"

    return {
        "status": "success",
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "unit": product.unit,
        "selling_price": product.selling_price,
        "cost_price": product.cost_price,
        "current_stock": current_stock,
        "min_reorder_level": rop,
        "lead_time_days": product.lead_time_days,
        "supplier_name": product.supplier_name,
        "stock_health": health,
    }


def get_low_stock_products(store_id: str, db: Session, limit: int = 15) -> Dict[str, Any]:
    """Scans store catalog and returns all items currently below their reorder point."""
    products = (
        db.query(models.Product)
        .filter(models.Product.store_id == store_id, models.Product.is_active.is_(True))
        .all()
    )

    depleted_items = []
    for prod in products:
        current_stock = InventoryService.get_current_stock(db, store_id, prod.id)
        if current_stock <= prod.min_reorder_level:
            depleted_items.append({
                "product_id": prod.id,
                "sku": prod.sku,
                "name": prod.name,
                "category": prod.category,
                "current_stock": current_stock,
                "reorder_point": prod.min_reorder_level,
                "supplier_name": prod.supplier_name,
                "cost_price": prod.cost_price,
                "is_out_of_stock": current_stock == 0,
            })

    depleted_items.sort(key=lambda x: (not x["is_out_of_stock"], x["current_stock"]))

    return {
        "status": "success",
        "total_low_stock_items": len(depleted_items),
        "items": depleted_items[:limit],
    }

