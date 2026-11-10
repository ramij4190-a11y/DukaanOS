"""Pydantic Schemas for AI Agent Invocations and Actions."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., example="Which products should I order tomorrow?")
    conversation_id: Optional[str] = "default-session"


class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class ProposedAction(BaseModel):
    action_type: str  # "CREATE_PURCHASE_ORDER", "RECONCILE_STOCK", "NONE"
    payload: Dict[str, Any]
    summary_text: str
    estimated_amount_inr: Optional[float] = None
    requires_human_approval: bool = True


class ChatResponse(BaseModel):
    reply_text: str
    tools_executed: List[str]
    proposed_action: Optional[ProposedAction] = None
    data_snapshot: Optional[Dict[str, Any]] = None


class ActionConfirmationRequest(BaseModel):
    action_type: str
    payload: Dict[str, Any]
    confirmed: bool = True

