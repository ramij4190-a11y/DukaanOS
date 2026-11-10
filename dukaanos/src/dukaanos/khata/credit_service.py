"""AI Khata & Customer Credit Risk Intelligence Engine.

Empowers Indian Kirana owners to manage the Udhar (Store Credit) economy:
- Tracks customer credit balance, transactions, and repayment history.
- Calculates dynamic Credit Default Risk Scores.
- Generates polite, culturally respectful WhatsApp payment reminders with UPI QR links.
"""

import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CustomerCreditProfile(BaseModel):
    customer_id: int
    name: str
    phone: str
    credit_limit: float = 5000.0
    current_balance: float = 0.0
    days_overdue: int = 0
    total_lifetime_purchases: float = 0.0
    successful_repayments_count: int = 0
    last_payment_date: Optional[str] = None


class CreditRiskEvaluation(BaseModel):
    customer_id: int
    name: str
    current_balance: float
    credit_limit: float
    credit_utilization_pct: float
    days_overdue: int
    risk_score: float  # [0.0, 1.0]
    risk_tier: str     # 'LOW', 'MODERATE', 'HIGH'
    recommended_action: str


class CreditService:
    """Manages customer credit balances, risk scoring, and payment recovery."""

    @staticmethod
    def evaluate_credit_risk(profile: CustomerCreditProfile) -> CreditRiskEvaluation:
        """Calculates dynamic default risk score based on credit utilization, overdue days, and repayment velocity."""
        utilization = min(profile.current_balance / max(profile.credit_limit, 1.0), 1.0)
        overdue_factor = min(profile.days_overdue / 45.0, 1.0)
        repayment_bonus = min(profile.successful_repayments_count * 0.05, 0.20)

        # Composite Risk Formula
        raw_score = (0.50 * utilization) + (0.45 * overdue_factor) - repayment_bonus
        score = max(0.0, min(round(raw_score, 3), 1.0))

        if score < 0.40:
            tier = "LOW"
            action = "Approve additional credit. Customer has healthy repayment record."
        elif score < 0.75:
            tier = "MODERATE"
            action = "Send gentle WhatsApp payment reminder. Cap additional credit."
        else:
            tier = "HIGH"
            action = "Freeze credit line. Immediate settlement required before further purchases."

        return CreditRiskEvaluation(
            customer_id=profile.customer_id,
            name=profile.name,
            current_balance=round(profile.current_balance, 2),
            credit_limit=round(profile.credit_limit, 2),
            credit_utilization_pct=round(utilization * 100, 1),
            days_overdue=profile.days_overdue,
            risk_score=score,
            risk_tier=tier,
            recommended_action=action,
        )

    @staticmethod
    def generate_payment_reminder(
        profile: CustomerCreditProfile,
        store_name: str = "Shree Ganesh Kirana",
        upi_vpa: str = "rameshkirana@upi",
        language: str = "hinglish",
    ) -> Dict[str, str]:
        """Generates a culturally polite WhatsApp reminder with embedded UPI payment link."""
        amt = profile.current_balance
        upi_pay_link = f"upi://pay?pa={upi_vpa}&pn={urllib.parse.quote(store_name)}&am={amt:.2f}&cu=INR"

        if language == "hindi":
            msg = (
                f"नमस्ते {profile.name} जी,\n\n"
                f"{store_name} से सादर प्रणाम।\n"
                f"आपके खाते का बकाया हिसाब ₹{amt:,.2f} है।\n"
                f"कृपया सुविधानुसार नीचे दिए गए लिंक से UPI द्वारा भुगतान कर दीजिए:\n\n"
                f"👉 UPI भुगतान लिंक: {upi_pay_link}\n\n"
                f"अगर आपने पहले ही भुगतान कर दिया है तो कृपया इस संदेश को अनदेखा करें।\n"
                f"धन्यवाद, {store_name}"
            )
        elif language == "english":
            msg = (
                f"Dear {profile.name},\n\n"
                f"Greetings from {store_name}.\n"
                f"This is a gentle reminder regarding your outstanding store credit of ₹{amt:,.2f}.\n"
                f"You can quickly settle via UPI using the link below:\n\n"
                f"👉 Pay via UPI: {upi_pay_link}\n\n"
                f"Thank you for being a valued customer!"
            )
        else:  # Hinglish
            msg = (
                f"Namaste {profile.name} Ji,\n\n"
                f"{store_name} ki taraf se pranaam.\n"
                f"Aapke bahi-khate ka pending balance ₹{amt:,.2f} hai.\n"
                f"Aap niche diye gaye link se aasaani se UPI se payment kar sakte hain:\n\n"
                f"👉 UPI Link: {upi_pay_link}\n\n"
                f"Agar aapne payment kar diya hai to kripya is message ko ignore karein.\n"
                f"Shukriya, {store_name}"
            )

        encoded_msg = urllib.parse.quote(msg)
        wa_url = f"https://wa.me/{profile.phone.replace('+', '').strip()}?text={encoded_msg}"

        return {
            "customer_name": profile.name,
            "customer_phone": profile.phone,
            "outstanding_amount": amt,
            "upi_deep_link": upi_pay_link,
            "raw_message": msg,
            "whatsapp_url": wa_url,
        }
