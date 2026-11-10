"""DukaanOS - Phase 4 AI Agent & LLM Operations Runner.

Demonstrates the Complete Forward Deployed Engineer (FDE) Workflow:
1. Multi-lingual / Hinglish natural language understanding
2. Deterministic tool invocation (Inventory, Forecasting, Procurement)
3. Safety guardrail verification (Budget caps & quantity limits)
4. Structured action proposal drafting (Draft Purchase Orders)
5. Human-in-the-loop shopkeeper confirmation & transactional execution
"""

import os
import sys
from pathlib import Path

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.backend.database import SessionLocal, Base, engine
from dukaanos.src.dukaanos.backend import models
from dukaanos.src.dukaanos.ai.agent.engine import RetailAgentEngine
from dukaanos.src.dukaanos.ai.agent.schema import ChatRequest
from dukaanos.src.dukaanos.ai.agent.guardrails import AgentGuardrails


def run_conversation_scenario(agent: RetailAgentEngine, scenario_title: str, user_message: str):
    """Executes a single conversational agent turn and prints reasoning and outputs."""
    print("\n" + "=" * 80)
    print(f"SCENARIO: {scenario_title}")
    print("=" * 80)
    print(f"👤 Shopkeeper: \"{user_message}\"")

    req = ChatRequest(message=user_message)
    res = agent.process_message(req)

    print(f"\n⚙️  Tools Executed: {res.tools_executed if res.tools_executed else 'None (Direct Response)'}")
    print(f"🤖 DukaanOS AI:\n{res.reply_text}")

    if res.proposed_action:
        act = res.proposed_action
        print("\n" + "-" * 50)
        print("📋 [PROPOSED ACTION PENDING SHOPKEEPER CONFIRMATION]")
        print(f"   Action Type:        {act.action_type}")
        print(f"   Estimated Amount:   ₹{act.estimated_amount_inr:,.2f}")
        print(f"   Approval Required:  {act.requires_human_approval}")
        print(f"   Summary:            {act.summary_text}")
        print("-" * 50)

    return res


def main():
    print("=" * 80)
    print("   DUKAANOS - AI-POWERED RETAIL INTELLIGENCE PLATFORM")
    print("   Phase 4: LLM Operations Agent & Action Engine")
    print("=" * 80)

    db = SessionLocal()
    store_id = "STORE-001"

    # Verify store exists
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        print("Error: Primary store STORE-001 not found. Please run run_phase_3.py first.")
        db.close()
        return

    agent = RetailAgentEngine(store_id=store_id, db=db)
    print(f"\nInitialized RetailAgentEngine for '{store.name}' ({store_id}).")

    # Simulate depleted stock for 2 items to trigger reorder workflow
    p_oil = db.query(models.Product).filter(models.Product.store_id == store_id, models.Product.sku == "OIL-004").first()
    if p_oil:
        from dukaanos.src.dukaanos.backend.services.inventory_service import InventoryService
        cur = InventoryService.get_current_stock(db, store_id, p_oil.id)
        if cur > 5:
            # Simulate a large weekend sale bringing stock below ROP
            InventoryService.post_ledger_event(db, store_id, p_oil.id, "SALE", -(cur - 3), p_oil.cost_price, "BULK-SALE", "Weekend Kirana counter rush")

    # Scenario 1: Hinglish Reorder Inquiry
    res1 = run_conversation_scenario(
        agent=agent,
        scenario_title="1. Multi-Lingual Reorder Recommendations",
        user_message="Kal ke liye kya order karna hai? Kon kon product order korte hobe?",
    )

    # Scenario 2: Hindi Stock Lookup
    res2 = run_conversation_scenario(
        agent=agent,
        scenario_title="2. Ground-Truth Inventory Ledger Lookup",
        user_message="Aashirvaad Atta ka stock kitna hai abhi?",
    )

    # Scenario 3: English Demand Forecasting
    res3 = run_conversation_scenario(
        agent=agent,
        scenario_title="3. Machine Learning Demand Forecast (LightGBM)",
        user_message="What is the 14-day demand forecast for Maggi Noodles?",
    )

    # Scenario 4: Safety Guardrails Verification
    print("\n" + "=" * 80)
    print("SCENARIO: 4. Safety Guardrails & Hallucination Prevention")
    print("=" * 80)
    unsafe_proposal = {
        "supplier_name": "Mega Wholesale Mandi",
        "total_order_amount_inr": 280000.0,  # Exceeds ₹1.5 Lakhs limit
        "items": [{"name": "Sugar 50kg Bags", "quantity": 800, "unit_cost": 2100.0}],  # Exceeds 500 units
    }
    is_valid, reason = AgentGuardrails.validate_purchase_order(unsafe_proposal)
    print(f"Testing Unsafe Autonomous Order (₹2,80,000 for 800 bags)...")
    print(f"  Guardrail Intercepted: {'BLOCKED 🛑' if not is_valid else 'ALLOWED'}")
    print(f"  Safety Rejection Reason: {reason}")

    # Scenario 5: Human-in-the-Loop Confirmation & Execution
    print("\n" + "=" * 80)
    print("SCENARIO: 5. Human-in-the-Loop Approval & Order Execution")
    print("=" * 80)
    if res1.proposed_action:
        print("👤 Shopkeeper clicks: [CONFIRM & APPROVE ORDER]")
        confirmed_payload = res1.proposed_action.payload
        exec_result = agent.execute_confirmed_action(
            action_type=res1.proposed_action.action_type,
            payload=confirmed_payload,
        )
        print(f"\n⚙️  Transaction Committed: {exec_result['status'].upper()} ✅")
        print(f"   Message:   {exec_result['message']}")
        print(f"   PO Number: {exec_result.get('po_number')}")
        print(f"   Amount:    ₹{exec_result.get('total_amount'):,.2f}")

    db.close()
    print("\n" + "=" * 80)
    print("   ✓ PHASE 4 AI OPERATIONS AGENT COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
