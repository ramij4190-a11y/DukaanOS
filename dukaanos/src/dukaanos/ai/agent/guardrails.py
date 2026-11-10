"""Safety Guardrails and Business Rule Validators for Agent Actions."""

from typing import Dict, Any, Tuple


class AgentGuardrails:
    """Enforces retail safety limits and business rule compliance before action proposal."""

    MAX_ORDER_BUDGET_INR = 150000.0  # ₹1.5 Lakh max order without special escalation
    MAX_UNITS_PER_ITEM = 500         # Prevents runaway ordering hallucinations

    @classmethod
    def validate_purchase_order(cls, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates proposed purchase order against budget and sanity limits."""
        total_amount = payload.get("total_order_amount_inr", 0.0)
        items = payload.get("items", [])

        if not items:
            return False, "Cannot propose an empty purchase order."

        if total_amount > cls.MAX_ORDER_BUDGET_INR:
            return False, f"Order total (₹{total_amount:,.2f}) exceeds single-order budget cap of ₹{cls.MAX_ORDER_BUDGET_INR:,.2f}."

        for item in items:
            qty = item.get("quantity", 0)
            name = item.get("name", "Product")
            if qty <= 0:
                return False, f"Invalid zero or negative quantity for '{name}'."
            if qty > cls.MAX_UNITS_PER_ITEM:
                return False, f"Quantity {qty} for '{name}' exceeds safe single-order ceiling of {cls.MAX_UNITS_PER_ITEM} units."

        return True, "Guardrail checks passed."

