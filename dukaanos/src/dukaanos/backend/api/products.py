"""Product Catalog Management API."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.api.deps import get_current_user
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService

router = APIRouter(prefix="/products", tags=["Product Catalog"])


@router.get("", response_model=List[schemas.ProductStockOut])
def list_products(
    category: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists products for the authenticated store, enriched with real-time stock and ROP status."""
    query = db.query(models.Product).filter(
        models.Product.store_id == current_user.store_id,
        models.Product.is_active.is_(True),
    )
    if category:
        query = query.filter(models.Product.category == category)

    products = query.all()
    results = []
    for prod in products:
        current_stock = InventoryService.get_current_stock(db, current_user.store_id, prod.id)
        rop = prod.min_reorder_level
        if current_stock == 0:
            status = "OUT_OF_STOCK"
        elif current_stock <= rop:
            status = "LOW_STOCK"
        else:
            status = "OK"

        results.append(schemas.ProductStockOut(
            id=prod.id,
            store_id=prod.store_id,
            sku=prod.sku,
            name=prod.name,
            category=prod.category,
            unit=prod.unit,
            cost_price=prod.cost_price,
            selling_price=prod.selling_price,
            min_reorder_level=prod.min_reorder_level,
            lead_time_days=prod.lead_time_days,
            supplier_name=prod.supplier_name,
            is_active=prod.is_active,
            current_stock=current_stock,
            reorder_point=rop,
            stock_status=status,
        ))

    return results


@router.post("", response_model=schemas.ProductOut)
def create_product(
    product_in: schemas.ProductCreate,
    initial_stock: int = Query(0, ge=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new product in the store catalog and optionally posts initial opening stock."""
    # Check duplicate SKU in this store
    existing = db.query(models.Product).filter(
        models.Product.store_id == current_user.store_id,
        models.Product.sku == product_in.sku,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"SKU '{product_in.sku}' already exists in your store.")

    product = models.Product(
        store_id=current_user.store_id,
        **product_in.model_dump(),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Post opening stock to ledger if initial_stock > 0
    if initial_stock > 0:
        InventoryService.post_ledger_event(
            db=db,
            store_id=current_user.store_id,
            product_id=product.id,
            event_type="OPENING_STOCK",
            quantity_change=initial_stock,
            unit_cost=product.cost_price,
            reference_id="INIT-SKU",
            notes="Initial opening inventory count",
        )

    return product

