"""Retail Intelligence & Morning Briefing API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.api.deps import get_current_user
from dukaanos.src.dukaanos.backend.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["Retail Intelligence"])


@router.get("/daily-brief", response_model=schemas.DailyBriefResponse)
def get_daily_morning_brief(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the morning business intelligence brief for the store owner:

    - Today's predicted sales ₹
    - Low-stock and out-of-stock SKU counts
    - Dynamic purchase suggestions calculated from ROP and lead times
    - Anomaly alerts
    """
    return IntelligenceService.get_morning_brief(db=db, store_id=current_user.store_id)

