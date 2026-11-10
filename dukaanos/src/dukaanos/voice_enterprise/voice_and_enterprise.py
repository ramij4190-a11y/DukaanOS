"""Indic Voice AI Copilot & Multi-Store Enterprise Management Engine.

Implements Phase 10:
1. Hands-free Indic voice slot filling & automated voice POS checkout.
2. Multi-store consolidated financial rollup and inventory visibility.
3. Cross-store inventory rebalancing algorithm (inter-store transfer recommendations).
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.services.sales_service import SalesService
from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
from dukaanos.src.dukaanos.multimodal.invoice_parser import InvoiceParserService


class VoiceEntityItem(BaseModel):
    raw_spoken_text: str
    quantity: int
    matched_product_id: Optional[int] = None
    matched_sku: Optional[str] = None
    matched_name: Optional[str] = None
    unit_price: float = 0.0
    line_total: float = 0.0


class VoicePOSCommandResult(BaseModel):
    spoken_utterance: str
    detected_intent: str
    detected_language: str
    extracted_items: List[VoiceEntityItem]
    total_bill_amount: float
    checkout_status: str
    voice_feedback_text: str


class StoreInventorySnapshot(BaseModel):
    store_id: str
    store_name: str
    sku: str
    product_name: str
    current_stock: int
    safety_stock: int
    min_reorder_level: int
    status: str  # 'DEFICIT', 'HEALTHY', 'SURPLUS'


class InterStoreTransferRecommendation(BaseModel):
    transfer_id: str
    sku: str
    product_name: str
    from_store_id: str
    from_store_name: str
    to_store_id: str
    to_store_name: str
    recommended_transfer_qty: int
    estimated_capital_protected_inr: float
    reason: str


class IndicVoiceService:
    """Processes spoken Hindi / Hinglish audio transcripts into deterministic POS actions."""

    # Hindi number words dictionary
    HINDI_NUMBERS = {
        "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
        "panch": 5, "chhe": 6, "che": 6, "saat": 7, "aath": 8,
        "nau": 9, "das": 10, "gyarah": 11, "barah": 12,
        "pandrah": 15, "bees": 20, "pachis": 25, "tees": 30,
        "chalis": 40, "pachaas": 50, "pachas": 50,
        "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10
    }

    @classmethod
    def parse_voice_utterance(
        cls,
        utterance: str,
        catalog: List[Dict[str, Any]],
    ) -> List[VoiceEntityItem]:
        """Extracts product entities and quantities from spoken vernacular utterances."""
        text = utterance.lower()
        items = []

        # Split multiple items joined by 'aur', 'and', or commas
        parts = re.split(r"\b(?:aur|and|,)\b", text)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Look for number / quantity tokens
            qty = 1
            words = part.split()
            found_num = False
            for w in words:
                if w in cls.HINDI_NUMBERS:
                    qty = cls.HINDI_NUMBERS[w]
                    found_num = True
                    break
                elif w.isdigit():
                    qty = int(w)
                    found_num = True
                    break

            # Strip command words like 'bill banao', 'ka bill', 'dalo', 'add karo'
            cleaned_name = re.sub(r"\b(?:bill|banao|dalo|add|karo|ka|ki|ke|bori|peti|packet|bottle|pkts|bag|bags)\b", "", part)
            cleaned_name = re.sub(r"\b\d+\b", "", cleaned_name).strip()

            matched_prod, score, status = InvoiceParserService.match_item_to_catalog(cleaned_name, catalog)
            if matched_prod and score >= 0.45:
                price = matched_prod.get("selling_price", matched_prod.get("cost_price", 100.0))
                items.append(
                    VoiceEntityItem(
                        raw_spoken_text=part,
                        quantity=qty,
                        matched_product_id=matched_prod["id"],
                        matched_sku=matched_prod["sku"],
                        matched_name=matched_prod["name"],
                        unit_price=price,
                        line_total=round(qty * price, 2),
                    )
                )

        return items

    @classmethod
    def execute_voice_pos_checkout(
        cls,
        db: Session,
        store_id: str,
        utterance: str,
        catalog: List[Dict[str, Any]],
    ) -> VoicePOSCommandResult:
        """Executes automated POS checkout from hands-free spoken voice input."""
        extracted = cls.parse_voice_utterance(utterance, catalog)

        if not extracted:
            return VoicePOSCommandResult(
                spoken_utterance=utterance,
                detected_intent="VOICE_POS_BILLING",
                detected_language="hinglish",
                extracted_items=[],
                total_bill_amount=0.0,
                checkout_status="NO_ITEMS_RECOGNIZED",
                voice_feedback_text="Maaf kijiye, koi product samajh nahi aaya. Kripya dobara boliye.",
            )

        total_amount = sum(it.line_total for it in extracted)
        idempotency_key = f"IDEMP-VOICE-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        sale_in = schemas.SalesCreate(
            payment_method="CASH",
            idempotency_key=idempotency_key,
            items=[
                schemas.SalesItemCreate(product_id=it.matched_product_id, quantity=it.quantity)
                for it in extracted
            ],
        )

        created_tx = SalesService.process_checkout(
            db=db,
            store_id=store_id,
            sales_in=sale_in,
            idempotency_key=idempotency_key,
        )

        # Synthesize audio voice response in polite Hindi
        item_summary = ", ".join([f"{it.quantity} {it.matched_name.split()[0]}" for it in extracted])
        feedback = (
            f"Theek hai Ramesh Ji! {item_summary} ka bill ban gaya hai. "
            f"Total hua ₹{created_tx.total_revenue:,.2f}. Stock ledger update ho gaya hai!"
        )

        return VoicePOSCommandResult(
            spoken_utterance=utterance,
            detected_intent="VOICE_POS_BILLING",
            detected_language="hinglish",
            extracted_items=extracted,
            total_bill_amount=created_tx.total_revenue,
            checkout_status="COMMITTED_TO_LEDGER",
            voice_feedback_text=feedback,
        )


class EnterpriseMultiStoreService:
    """Manages multi-branch store operations and cross-store inventory rebalancing."""

    @staticmethod
    def audit_branch_inventory(
        store_snapshots: List[StoreInventorySnapshot],
    ) -> List[StoreInventorySnapshot]:
        """Categorizes branch inventory into DEFICIT, HEALTHY, and SURPLUS."""
        audited = []
        for s in store_snapshots:
            if s.current_stock < s.safety_stock:
                status = "DEFICIT"
            elif s.current_stock > (s.min_reorder_level * 2):
                status = "SURPLUS"
            else:
                status = "HEALTHY"

            s_copy = s.model_copy()
            s_copy.status = status
            audited.append(s_copy)
        return audited

    @staticmethod
    def generate_inter_store_transfers(
        store_snapshots: List[StoreInventorySnapshot],
        unit_retail_value: float = 245.0,
    ) -> List[InterStoreTransferRecommendation]:
        """Generates cross-store transfer recommendations to resolve stockouts from sibling surpluses."""
        audited = EnterpriseMultiStoreService.audit_branch_inventory(store_snapshots)
        deficits = [s for s in audited if s.status == "DEFICIT"]
        surpluses = [s for s in audited if s.status == "SURPLUS"]

        recommendations = []
        count = 101

        for d in deficits:
            for s in surpluses:
                if d.sku == s.sku and d.store_id != s.store_id:
                    needed = d.safety_stock - d.current_stock
                    available_excess = s.current_stock - s.min_reorder_level
                    if available_excess <= 0:
                        continue

                    transfer_qty = min(needed, available_excess)
                    if transfer_qty > 0:
                        capital_saved = transfer_qty * unit_retail_value
                        recommendations.append(
                            InterStoreTransferRecommendation(
                                transfer_id=f"TRF-{count}",
                                sku=d.sku,
                                product_name=d.product_name,
                                from_store_id=s.store_id,
                                from_store_name=s.store_name,
                                to_store_id=d.store_id,
                                to_store_name=d.store_name,
                                recommended_transfer_qty=transfer_qty,
                                estimated_capital_protected_inr=round(capital_saved, 2),
                                reason=(
                                    f"Transfer {transfer_qty} units from {s.store_name} (Excess) to "
                                    f"{d.store_name} (Stockout risk) to prevent ₹{capital_saved:,.2f} in lost sales."
                                ),
                            )
                        )
                        count += 1
                        # Adjust temporary stock in simulation
                        s.current_stock -= transfer_qty
                        d.current_stock += transfer_qty

        return recommendations
