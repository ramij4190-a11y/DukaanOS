"""Main API Router aggregating all sub-domain endpoints."""

from fastapi import APIRouter
from dukaanos.src.dukaanos.backend.api import (
    auth, products, inventory, sales, purchase_orders, intelligence, multimodal, sync, khata, syndicate
)
from dukaanos.src.dukaanos.ai.router import ai_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(inventory.router)
api_router.include_router(sales.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(intelligence.router)
api_router.include_router(ai_router)
api_router.include_router(multimodal.router)
api_router.include_router(sync.router)
api_router.include_router(khata.router)
api_router.include_router(syndicate.router)

