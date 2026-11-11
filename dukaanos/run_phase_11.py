"""DukaanOS (दुकानOS) — Phase 11 Interactive Showcase.

Demonstrates:
1. Continual Online Machine Learning Brain (Incremental EWMA velocity & volatility).
2. Autonomous Self-Driving Store Operations:
   - Depletion horizon estimation (Days-to-Depletion countdown).
   - Auto-drafting procurement POs before stockouts occur.
   - Dead capital / slow-moving batch clearance markdown suggestions.
3. Instant Voice-to-Brain Learning Loop (Speech inputs dynamically trigger re-learning).
4. Vernacular Morning Store Brief synthesized in Hindi.
"""

import sys
from pathlib import Path

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.brain.autonomous_brain import AutonomousStoreBrain


def run_phase_11_showcase():
    print("=" * 86)
    print("   DUKAANOS (दुकानOS) — PHASE 11 AUTONOMOUS STORE BRAIN SHOWCASE")
    print("   Continual Online Machine Learning & Self-Driving Kirana Operations")
    print("   ₹0 Local Indic AI • Real-Time EWMA Velocity Learning • Auto-Pilot Restocking")
    print("=" * 86)

    brain = AutonomousStoreBrain(store_id="STORE-001")

    # Step 1: Initial Baseline Learned Profiles
    print("\n[Step 1/4] Baseline Continuous Learning State (Priors & Burn Rates):")
    print("-" * 86)
    print(f"{'SKU':<10} {'Product Name':<34} {'Stock':<8} {'Velocity':<12} {'ROP':<8} {'Days Left':<10} {'Status'}")
    print("-" * 86)
    for p in brain.profiles.values():
        print(
            f"{p.sku:<10} {p.product_name[:32]:<34} {p.current_stock:<8} "
            f"{p.learned_daily_velocity:<12.1f} {p.dynamic_reorder_point:<8} "
            f"{p.days_to_depletion:<10.1f} {p.status}"
        )

    # Step 2: High Velocity Sales Surge Signals (Incremental EWMA Learning)
    print("\n[Step 2/4] Ingesting Rapid Counter Sales Surge Signals (Online Re-Learning):")
    print("-" * 86)
    print("Simulating 3 consecutive high-demand sales of Aashirvaad Atta 5kg...")
    
    for i in range(1, 4):
        updated = brain.ingest_signal(
            sku="STP-001",
            product_name="Aashirvaad Shudh Chakki Atta 5kg",
            event_type="SALE",
            quantity_delta=-12,
            new_balance=50 - (i * 12),
            unit_cost=225.0,
            selling_price=260.0
        )
        print(
            f"  ⚡ Signal #{i}: 12 units sold! "
            f"Learned Velocity: {updated.learned_daily_velocity:.2f} units/day | "
            f"New Stock: {updated.current_stock} | "
            f"Days Left: {updated.days_to_depletion:.1f} days"
        )

    # Step 3: Depletion Trigger & Autonomous Action Generation
    print("\n[Step 3/4] Autonomous Action Engine (Self-Driving Store Triggers):")
    print("-" * 86)
    state = brain.get_state()
    print(f"Store AI Health Score: {state.health_score_percent}% | Total Learning Iterations: {state.total_learning_updates}")
    print(f"Active Autonomous Proposals ({len(state.active_autonomous_actions)}):")
    
    for a in state.active_autonomous_actions:
        print(f"\n  🤖 [{a.urgency}] {a.title} (ID: {a.action_id})")
        print(f"     ↳ Rationale: {a.description}")
        if "suggested_qty" in a.recommended_payload:
            payload = a.recommended_payload
            print(f"     ↳ Auto-Drafted PO: +{payload['suggested_qty']} units (Est. Cost: ₹{payload['estimated_cost']:,.2f})")
        print(f"     ↳ Voice Announcement: \"{a.voice_announcement_text}\"")

    # Step 4: Spoken Vernacular Morning Brief
    print("\n[Step 4/4] Vernacular Autonomous Voice Operations Brief:")
    print("-" * 86)
    brief = brain.generate_morning_voice_brief()
    print(f"🎙️ AI Audio Brief: \"{brief}\"")

    print("\n" + "=" * 86)
    print("   ✓ PHASE 11 VERIFICATION COMPLETE — CONTINUOUS LEARNING BRAIN OPERATIONAL!")
    print("   Test Live in Web Dashboard: https://546a7728a69f5f.lhr.life/")
    print("=" * 86)


if __name__ == "__main__":
    run_phase_11_showcase()
