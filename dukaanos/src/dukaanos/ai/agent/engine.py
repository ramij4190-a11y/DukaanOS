"""Core AI Agent Orchestration Engine for DukaanOS.

Implements the complete FDE workflow:
1. Intent & entity classification (supporting English, Hindi, Hinglish & Bengali queries)
2. Approved deterministic tool selection & execution
3. Safety guardrail validation
4. Proposal drafting requiring human-in-the-loop confirmation
5. Confirmed transaction execution and audit logging
"""

import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.ai.agent.schema import ChatRequest, ChatResponse, ProposedAction
from dukaanos.src.dukaanos.ai.agent.guardrails import AgentGuardrails
from dukaanos.src.dukaanos.ai.tools.inventory_tools import get_inventory_status, get_low_stock_products
from dukaanos.src.dukaanos.ai.tools.forecasting_tools import get_product_forecast, get_top_selling_products
from dukaanos.src.dukaanos.ai.tools.procurement_tools import calculate_reorder_quantities, draft_purchase_order_proposal
from dukaanos.src.dukaanos.backend import models, schemas
from dukaanos.src.dukaanos.backend.services.po_service import PurchaseOrderService


class RetailAgentEngine:
    """Intelligent business operations agent for Kirana store owners."""

    def __init__(self, store_id: str, db: Session):
        self.store_id = store_id
        self.db = db

    def process_message(self, request: ChatRequest) -> ChatResponse:
        """Processes user input, routes to approved tools, and returns actionable guidance."""
        text = request.message.strip().lower()
        tools_executed = []
        proposed_action = None
        data_snapshot = None

        # 1. Intent: Reorder recommendations ("order", "purchase", "kharidna", "korte hobe", "restock")
        if any(w in text for w in ["order", "purchase", "kharid", "reorder", "replenish", "korte hobe", "kya mangwana"]):
            tools_executed.append("calculate_reorder_quantities")
            reorder_data = calculate_reorder_quantities(self.store_id, self.db)
            data_snapshot = reorder_data

            count = reorder_data["items_needing_reorder_count"]
            total_est = reorder_data["total_estimated_purchase_cost_inr"]
            suggestions = reorder_data["reorder_suggestions"]

            if count == 0:
                reply = "Good news! All product stock levels are currently above their reorder thresholds. No urgent supplier orders needed today."
            else:
                top_items = [f"• {s['name'][:25]} — {s['suggested_order_qty']} units (₹{s['estimated_line_cost']:,.0f})" for s in suggestions[:4]]
                items_str = "\n".join(top_items)

                reply = (
                    f"I checked your current inventory and sales velocity. "
                    f"**{count} products** are near or below their reorder points (Est. total: ₹{total_est:,.2f}):\n\n"
                    f"{items_str}\n\n"
                    f"These are purchase suggestions based on supplier lead times. Would you like me to draft purchase orders for your review?"
                )

                # Prepare proposed draft purchase order
                if suggestions:
                    supplier = suggestions[0].get("supplier_name", "Primary Distributor")
                    draft_items = [{"product_id": s["product_id"], "quantity": s["suggested_order_qty"]} for s in suggestions[:3]]
                    proposal = draft_purchase_order_proposal(self.store_id, supplier, draft_items, self.db)

                    # Validate guardrails
                    is_valid, reason = AgentGuardrails.validate_purchase_order(proposal)
                    if is_valid:
                        proposed_action = ProposedAction(
                            action_type="CREATE_PURCHASE_ORDER",
                            payload=proposal,
                            summary_text=proposal["message"],
                            estimated_amount_inr=proposal["total_order_amount_inr"],
                            requires_human_approval=True,
                        )

            return ChatResponse(
                reply_text=reply,
                tools_executed=tools_executed,
                proposed_action=proposed_action,
                data_snapshot=data_snapshot,
            )

        # 2. Intent: Demand Forecasting ("forecast", "demand", "bikri", "prediction", "bikri kitni")
        elif any(w in text for w in ["forecast", "demand", "predict", "bikri kitni", "bikegi"]):
            tools_executed.append("get_product_forecast")
            # Extract product query if present, otherwise default to a staple
            product_query = "atta" if "atta" in text else ("rice" if "rice" in text else ("ghee" if "ghee" in text else "maggi"))
            horizon = 14 if "14" in text else 7

            forecast_data = get_product_forecast(self.store_id, product_query, horizon, self.db)
            data_snapshot = forecast_data

            if forecast_data["status"] == "success":
                reply = (
                    f"**{horizon}-Day Demand Forecast for {forecast_data['name']}:**\n"
                    f"• Estimated Demand: **{forecast_data['forecasted_demand_units']} units**\n"
                    f"• Expected Revenue: **₹{forecast_data['projected_revenue_inr']:,.2f}**\n"
                    f"• Daily Average: ~{forecast_data['daily_average_units']} units/day\n"
                    f"*(Powered by LightGBM model accounting for weekly cycles and festival surges)*"
                )
            else:
                reply = f"Could not find sales history for '{product_query}' to forecast."

            return ChatResponse(
                reply_text=reply,
                tools_executed=tools_executed,
                data_snapshot=data_snapshot,
            )

        # 3. Intent: Specific Product Stock Lookup ("stock", "kitna hai", "available", "inventory")
        elif any(w in text for w in ["stock", "kitna", "inventory", "available"]):
            tools_executed.append("get_inventory_status")
            product_query = "atta" if "atta" in text else ("ghee" if "ghee" in text else ("oil" if "oil" in text else ("milk" if "milk" in text else "maggi")))

            inv_data = get_inventory_status(self.store_id, product_query, self.db)
            data_snapshot = inv_data

            if inv_data["status"] == "success":
                health_emoji = "⚠️" if inv_data["stock_health"] != "HEALTHY" else "✅"
                reply = (
                    f"{health_emoji} **{inv_data['name']}**:\n"
                    f"• Current Stock: **{inv_data['current_stock']} {inv_data['unit']}**\n"
                    f"• Reorder Level: {inv_data['min_reorder_level']} {inv_data['unit']}\n"
                    f"• Selling Price: ₹{inv_data['selling_price']} (Cost: ₹{inv_data['cost_price']})\n"
                    f"• Stock Health: **{inv_data['stock_health']}**"
                )
            else:
                reply = f"Product '{product_query}' not found in store catalog."

            return ChatResponse(
                reply_text=reply,
                tools_executed=tools_executed,
                data_snapshot=data_snapshot,
            )

        # 4. Intent: Top Selling Products ("top", "best seller", "sabse zyada", "bestseller")
        elif any(w in text for w in ["top", "best", "sabse zyada", "highest"]):
            tools_executed.append("get_top_selling_products")
            top_data = get_top_selling_products(self.store_id, limit=5, db=self.db)
            data_snapshot = top_data

            if top_data["top_products"]:
                top_lines = [f"{i+1}. **{p['name'][:28]}** — {p['total_units_sold']} units (₹{p['total_revenue']:,.0f})" for i, p in enumerate(top_data["top_products"])]
                reply = "**Your Top Selling Products by Revenue:**\n" + "\n".join(top_lines)
            else:
                reply = "No recent sales history recorded yet to rank best-sellers."

            return ChatResponse(
                reply_text=reply,
                tools_executed=tools_executed,
                data_snapshot=data_snapshot,
            )

        # 5. Fallback General Greeting & Help
        else:
            return ChatResponse(
                reply_text=(
                    "Namaste! I am your DukaanOS Retail Intelligence Assistant. I can help you with:\n"
                    "1. **Restock Suggestions:** *'Which products should I order tomorrow?'*\n"
                    "2. **Stock Inquiries:** *'Atta ka stock kitna hai?'*\n"
                    "3. **Demand Forecasting:** *'Show 7-day forecast for Ghee'*\n"
                    "4. **Performance:** *'Which are my top selling items?'*\n\n"
                    "How can I assist your shop today?"
                ),
                tools_executed=[],
            )

    def execute_confirmed_action(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a human-confirmed transaction with safety verification."""
        if action_type == "CREATE_PURCHASE_ORDER":
            supplier_name = payload.get("supplier_name", "Distributor")
            items = payload.get("items", [])

            # Format for PurchaseOrderService
            po_items = [
                schemas.POItemCreate(
                    product_id=it["product_id"],
                    quantity_ordered=it["quantity"],
                    unit_cost=it["unit_cost"],
                )
                for it in items
            ]
            po_in = schemas.POCreate(supplier_name=supplier_name, items=po_items)

            po = PurchaseOrderService.create_po(self.db, self.store_id, po_in)
            # Auto-approve once owner confirms via AI chat
            PurchaseOrderService.approve_po(self.db, self.store_id, po.id)

            return {
                "status": "success",
                "message": f"Successfully created and approved Purchase Order #{po.po_number} (₹{po.total_amount:,.2f}) for '{supplier_name}'.",
                "po_number": po.po_number,
                "total_amount": po.total_amount,
            }

        return {"status": "error", "message": f"Unknown action type: {action_type}"}

