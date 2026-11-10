"""AI Khata & Credit Intelligence API Endpoints."""

from fastapi import APIRouter
from dukaanos.src.dukaanos.khata.credit_service import (
    CreditService, CustomerCreditProfile, CreditRiskEvaluation
)

router = APIRouter(prefix="/khata", tags=["AI Khata & Credit Risk"])


@router.post("/risk-evaluation", response_model=CreditRiskEvaluation)
def evaluate_customer_credit(profile: CustomerCreditProfile):
    """Evaluates customer credit default risk and returns risk tier."""
    return CreditService.evaluate_credit_risk(profile)


@router.post("/generate-reminder")
def generate_whatsapp_payment_reminder(
    profile: CustomerCreditProfile,
    store_name: str = "Shree Ganesh Kirana",
    upi_vpa: str = "rameshkirana@upi",
    language: str = "hinglish",
):
    """Generates polite WhatsApp payment reminder with embedded UPI payment link."""
    return CreditService.generate_payment_reminder(
        profile=profile,
        store_name=store_name,
        upi_vpa=upi_vpa,
        language=language,
    )

