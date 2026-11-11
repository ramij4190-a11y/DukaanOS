"""Autonomous Kirana Brain API Endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any

from dukaanos.src.dukaanos.brain.autonomous_brain import (
    AutonomousStoreBrain, StoreBrainState, get_store_brain
)

router = APIRouter(prefix="/brain", tags=["Autonomous Kirana Brain"])


class IngestSignalRequest(BaseModel):
    store_id: str = "STORE-001"
    sku: str
    product_name: str
    event_type: str  # 'SALE', 'PURCHASE', 'DAMAGE_EXPIRED', 'ADJUSTMENT'
    quantity_delta: int
    new_balance: int
    unit_cost: float = 100.0
    selling_price: float = 125.0
    category: str = "General"


class ExecuteActionRequest(BaseModel):
    store_id: str = "STORE-001"
    action_id: str


@router.get("/status", response_model=StoreBrainState)
def get_brain_status(store_id: str = Query("STORE-001")):
    """Returns the continuous learning state, autonomous actions, and morning voice brief."""
    brain = get_store_brain(store_id)
    return brain.get_state()


@router.post("/ingest-signal")
def ingest_signal(req: IngestSignalRequest):
    """Ingests a transactional signal to trigger real-time online ML re-learning."""
    brain = get_store_brain(req.store_id)
    profile = brain.ingest_signal(
        sku=req.sku,
        product_name=req.product_name,
        event_type=req.event_type,
        quantity_delta=req.quantity_delta,
        new_balance=req.new_balance,
        unit_cost=req.unit_cost,
        selling_price=req.selling_price,
        category=req.category,
    )
    return {
        "status": "SUCCESS",
        "message": f"Learned profile updated for {req.product_name}",
        "profile": profile,
        "brain_health_score": brain.get_state().health_score_percent,
    }


@router.post("/execute-action")
def execute_autonomous_action(req: ExecuteActionRequest):
    """Approves and executes an autonomous action proposal (e.g. PO dispatch)."""
    brain = get_store_brain(req.store_id)
    success = brain.execute_action(req.action_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Action '{req.action_id}' not found.")
    return {
        "status": "EXECUTED",
        "action_id": req.action_id,
        "message": f"Autonomous action '{req.action_id}' successfully executed into store pipeline."
    }
