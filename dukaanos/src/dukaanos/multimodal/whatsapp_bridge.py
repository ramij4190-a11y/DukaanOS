"""WhatsApp Mandi Bridge & Omnichannel Webhook Service.

Enables small retailers to interact with wholesale distributors and DukaanOS via WhatsApp:
- Generates 1-click WhatsApp purchase order links (wa.me) in Hindi, Hinglish, and English.
- Simulates inbound WhatsApp webhook message parsing (e.g. stock receipts or inquiries).
"""

import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WhatsAppOrderItem(BaseModel):
    name: str
    quantity: int
    unit: str = "units"


class WhatsAppOrderRequest(BaseModel):
    store_name: str = "Shree Ganesh Kirana"
    supplier_phone: str = "919876543210"
    supplier_name: str = "Mandi Wholesaler"
    language: str = "hinglish"  # 'hindi', 'hinglish', 'english'
    items: List[WhatsAppOrderItem]


class WhatsAppBridgeService:
    """Manages localized WhatsApp formatting and inbound message processing."""

    @staticmethod
    def format_po_message(req: WhatsAppOrderRequest) -> str:
        """Constructs localized, human-friendly WhatsApp procurement message text."""
        date_str = datetime.now().strftime("%d-%m-%Y")

        if req.language == "hindi":
            lines = [
                f"*दुकानOS मंडी आर्डर*",
                f"दुकान: {req.store_name}",
                f"तारीख: {date_str}",
                f"नमस्ते भाईजी, कृपया कल सुबह निम्नलिखित सामान भेज दीजिए:",
                "",
            ]
            for i, it in enumerate(req.items, 1):
                lines.append(f"{i}. {it.name} — {it.quantity} {it.unit}")
            lines.append("")
            lines.append("बिल दुकान के नाम पर बना दीजिएगा। धन्यवाद!")

        elif req.language == "english":
            lines = [
                f"*DUKAANOS PURCHASE ORDER*",
                f"Store: {req.store_name}",
                f"Date: {date_str}",
                f"Dear {req.supplier_name}, please dispatch the following items:",
                "",
            ]
            for i, it in enumerate(req.items, 1):
                lines.append(f"{i}. {it.name} — {it.quantity} {it.unit}")
            lines.append("")
            lines.append("Please issue invoice to store name. Thank you.")

        else:  # Hinglish (Default)
            lines = [
                f"*DUKAANOS MANDI ORDER*",
                f"Store: {req.store_name}",
                f"Date: {date_str}",
                f"Bhaiji, please dispatch following items tomorrow morning:",
                "",
            ]
            for i, it in enumerate(req.items, 1):
                lines.append(f"{i}. {it.name} — {it.quantity} {it.unit}")
            lines.append("")
            lines.append("Bill shop ke naam pe bana dijiyega. Shukriya!")

        return "\n".join(lines)

    @classmethod
    def generate_whatsapp_link(cls, req: WhatsAppOrderRequest) -> Dict[str, str]:
        """Generates a direct wa.me link with URL-encoded procurement message."""
        msg_text = cls.format_po_message(req)
        encoded_text = urllib.parse.quote(msg_text)
        clean_phone = req.supplier_phone.replace("+", "").replace("-", "").strip()
        link = f"https://wa.me/{clean_phone}?text={encoded_text}"

        return {
            "supplier_phone": clean_phone,
            "language": req.language,
            "raw_message": msg_text,
            "whatsapp_url": link,
        }

    @staticmethod
    def parse_inbound_whatsapp_message(sender_phone: str, message_body: str) -> Dict[str, Any]:
        """Simulates processing of inbound WhatsApp text from storekeeper or supplier."""
        body_lower = message_body.lower()

        # Check intent
        if "stock" in body_lower or "kitna hai" in body_lower or "baki" in body_lower:
            intent = "STOCK_INQUIRY"
        elif "aaya" in body_lower or "delivered" in body_lower or "received" in body_lower:
            intent = "DELIVERY_RECEIPT"
        elif "order" in body_lower or "bhejo" in body_lower:
            intent = "NEW_PURCHASE_ORDER"
        else:
            intent = "GENERAL_CONVERSATION"

        return {
            "sender_phone": sender_phone,
            "received_at": datetime.now().isoformat(),
            "raw_message": message_body,
            "detected_intent": intent,
            "status": "PROCESSED",
        }

