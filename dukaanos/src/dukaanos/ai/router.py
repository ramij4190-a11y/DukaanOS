"""FastAPI Router for AI Operations Agent."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.backend.api.deps import get_current_user
from dukaanos.src.dukaanos.ai.agent.schema import ChatRequest, ChatResponse, ActionConfirmationRequest
from dukaanos.src.dukaanos.ai.agent.engine import RetailAgentEngine

ai_router = APIRouter(prefix="/ai", tags=["AI Operations Assistant"])


@router_chat := ai_router.post("/chat", response_model=ChatResponse)
def chat_with_retail_agent(
    request: ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Processes conversational natural-language queries (English, Hindi, Hinglish), invokes approved tools,

    and returns actionable intelligence or human-approval action drafts.
    """
    engine = RetailAgentEngine(store_id=current_user.store_id, db=db)
    return engine.process_message(request)


@router_action := ai_router.post("/action/confirm")
def confirm_and_execute_agent_action(
    req: ActionConfirmationRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Human-in-the-loop execution endpoint: commits owner-confirmed action payload to the database."""
    if not req.confirmed:
        return {"status": "cancelled", "message": "Action proposal discarded by shopkeeper."}

    engine = RetailAgentEngine(store_id=current_user.store_id, db=db)
    return engine.execute_confirmed_action(action_type=req.action_type, payload=req.payload)

