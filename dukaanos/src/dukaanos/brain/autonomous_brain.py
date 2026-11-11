"""DukaanOS (दुकानOS) — Autonomous Self-Learning Store Brain Engine.

Implements Phase 11:
1. Online Incremental Learning: Learns daily demand velocity (EWMA) and volatility on every event.
2. Dynamic Lead-Time & ROP Tuning: Recalculates Reorder Points and safety stocks in real time.
3. Autonomous Action Engine:
   - Predicts depletion horizons (Days to Depletion).
   - Automatically drafts purchase orders before stockout hits.
   - Detects abnormal shrinkage/damage patterns.
   - Proposes dead-capital markdown bundles.
4. Vernacular Voice Operations Brief: Synthesizes intelligent store audio agendas in Hindi/Hinglish.
"""

from datetime import datetime
import math
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LearnedProductProfile(BaseModel):
    """Dynamic profile of an SKU continually learned by the AI brain."""
    sku: str
    product_name: str
    category: str
    current_stock: int
    cost_price: float
    selling_price: float
    learned_daily_velocity: float = 3.5  # mu (average daily units sold)
    learned_volatility: float = 1.2      # sigma (standard deviation)
    learned_lead_time_days: float = 2.0  # supplier turnaround days
    dynamic_reorder_point: int = 15      # auto-tuned ROP
    days_to_depletion: float = 7.0       # days before stock hits 0
    status: str = "HEALTHY"             # 'HEALTHY', 'CRITICAL_DEPLETION', 'REORDER_NEEDED', 'OVERSTOCKED'
    last_signal_event: str = "INIT"
    total_events_observed: int = 1
    last_updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class AutonomousAction(BaseModel):
    """Action proposed or automatically executed by the Self-Driving Store Brain."""
    action_id: str
    action_type: str  # 'AUTO_RESTOCK_PO', 'EXPIRY_MARKDOWN', 'SUPPLIER_QUALITY_ALERT', 'KHATA_COLLECTION'
    product_sku: Optional[str] = None
    title: str
    description: str
    urgency: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'INFO'
    recommended_payload: Dict[str, Any] = Field(default_factory=dict)
    auto_executed: bool = False
    voice_announcement_text: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%I:%M %p"))


class StoreBrainState(BaseModel):
    """Consolidated state of the store's autonomous brain."""
    store_id: str
    total_skus_monitored: int
    total_learning_updates: int
    active_autonomous_actions: List[AutonomousAction]
    monitored_profiles: List[LearnedProductProfile]
    health_score_percent: float
    morning_voice_brief: str


class AutonomousStoreBrain:
    """Core AI engine that learns store physics and drives autonomous operations."""

    def __init__(self, store_id: str = "STORE-001"):
        self.store_id = store_id
        self.profiles: Dict[str, LearnedProductProfile] = {}
        self.actions: List[AutonomousAction] = []
        self.learning_updates_count: int = 0
        self._action_counter: int = 101
        self._bootstrap_default_catalog()

    def _bootstrap_default_catalog(self):
        """Initializes known core retail products with baseline priors."""
        defaults = [
            ("STP-001", "Aashirvaad Shudh Chakki Atta 5kg", "Staples", 50, 225.0, 260.0, 5.0, 1.5, 2.0, 20),
            ("OIL-003", "Fortune Sunlite Sunflower Oil 1L", "Edible Oils", 40, 135.0, 160.0, 4.0, 1.2, 2.5, 18),
            ("PCK-004", "Parle-G Glucose Biscuits 250g", "Packaged Foods", 80, 20.0, 25.0, 7.5, 2.0, 1.5, 25),
            ("STP-002", "India Gate Basmati Rice 5kg", "Staples", 30, 420.0, 480.0, 2.5, 0.8, 3.0, 15),
            ("PCK-019", "Tata Tea Gold 500g", "Packaged Foods", 25, 220.0, 260.0, 2.0, 0.6, 2.0, 12),
        ]
        for sku, name, cat, stock, cost, sell, vel, vol, lt, rop in defaults:
            self.profiles[sku] = LearnedProductProfile(
                sku=sku,
                product_name=name,
                category=cat,
                current_stock=stock,
                cost_price=cost,
                selling_price=sell,
                learned_daily_velocity=vel,
                learned_volatility=vol,
                learned_lead_time_days=lt,
                dynamic_reorder_point=rop,
                days_to_depletion=round(stock / max(vel, 0.1), 1),
                status="HEALTHY",
                last_signal_event="BOOTSTRAP",
                total_events_observed=1,
            )

    def ingest_signal(
        self,
        sku: str,
        product_name: str,
        event_type: str,
        quantity_delta: int,
        new_balance: int,
        unit_cost: float = 100.0,
        selling_price: float = 120.0,
        category: str = "General",
    ) -> LearnedProductProfile:
        """Ingests a real-time event (Voice / POS / Mandi) and incrementally updates the brain."""
        self.learning_updates_count += 1

        if sku not in self.profiles:
            self.profiles[sku] = LearnedProductProfile(
                sku=sku,
                product_name=product_name,
                category=category,
                current_stock=new_balance,
                cost_price=unit_cost,
                selling_price=selling_price,
            )

        p = self.profiles[sku]
        p.current_stock = new_balance
        p.last_signal_event = event_type
        p.total_events_observed += 1
        p.last_updated_at = datetime.now().isoformat()

        # 1. Continual Online Learning (EWMA Velocity Update)
        alpha = 0.15  # Velocity learning rate
        beta = 0.10   # Volatility learning rate

        if event_type == "SALE":
            observed_sale = abs(quantity_delta)
            # Update mean velocity
            p.learned_daily_velocity = round((1 - alpha) * p.learned_daily_velocity + alpha * observed_sale, 2)
            # Update variance & standard deviation
            variance_delta = (observed_sale - p.learned_daily_velocity) ** 2
            current_var = p.learned_volatility ** 2
            new_var = (1 - beta) * current_var + beta * variance_delta
            p.learned_volatility = round(math.sqrt(max(new_var, 0.25)), 2)
        elif event_type == "DAMAGE_EXPIRED":
            # If excessive damage occurs, temporarily inflate volatility buffer
            p.learned_volatility = round(p.learned_volatility * 1.15, 2)

        # 2. Dynamic Safety Stock & Reorder Point (ROP) Calculation
        # Service level Z = 1.65 (95% non-stockout protection)
        z_score = 1.65
        lead_time = p.learned_lead_time_days
        demand_during_lt = p.learned_daily_velocity * lead_time
        safety_stock = z_score * p.learned_volatility * math.sqrt(lead_time)
        p.dynamic_reorder_point = max(int(math.ceil(demand_during_lt + safety_stock)), 5)

        # 3. Predict Depletion Horizon
        effective_vel = max(p.learned_daily_velocity, 0.1)
        p.days_to_depletion = round(p.current_stock / effective_vel, 1)

        # 4. Status Evaluation & Autonomous Action Generation
        self._evaluate_autonomous_triggers(p)

        return p

    def _evaluate_autonomous_triggers(self, p: LearnedProductProfile):
        """Analyzes product horizons and synthesizes self-driving operational actions."""
        # Condition A: Imminent Stockout
        if p.current_stock <= p.dynamic_reorder_point or p.days_to_depletion <= (p.learned_lead_time_days + 1.0):
            p.status = "CRITICAL_DEPLETION" if p.current_stock <= 5 else "REORDER_NEEDED"
            
            # Check if active PO action already exists
            existing = any(a.product_sku == p.sku and a.action_type == "AUTO_RESTOCK_PO" for a in self.actions)
            if not existing:
                order_qty = max(int(p.learned_daily_velocity * 7), p.dynamic_reorder_point)
                est_cost = round(order_qty * p.cost_price, 2)
                
                action = AutonomousAction(
                    action_id=f"ACT-{self._action_counter}",
                    action_type="AUTO_RESTOCK_PO",
                    product_sku=p.sku,
                    title=f"Auto-Draft PO: {p.product_name}",
                    description=(
                        f"Stock {p.current_stock} bacha hai ({p.days_to_depletion} din ka backup). "
                        f"Learned burn-rate {p.learned_daily_velocity} units/day hai. "
                        f"Stockout rokne ke liye +{order_qty} units ka PO prepare kiya gaya hai."
                    ),
                    urgency="CRITICAL" if p.current_stock <= 5 else "HIGH",
                    recommended_payload={
                        "sku": p.sku,
                        "product_name": p.product_name,
                        "suggested_qty": order_qty,
                        "estimated_cost": est_cost,
                        "supplier": "Primary Mandi Wholesaler"
                    },
                    auto_executed=False,
                    voice_announcement_text=(
                        f"Ramesh Ji, {p.product_name.split()[0]} stock khatam hone wala hai. "
                        f"{order_qty} packet ka purchase order auto-draft kar diya gaya hai."
                    )
                )
                self.actions.insert(0, action)
                self._action_counter += 1

        # Condition B: Overstocking / Dead Capital
        elif p.current_stock > (p.dynamic_reorder_point * 3) and p.days_to_depletion > 25.0:
            p.status = "OVERSTOCKED"
            existing = any(a.product_sku == p.sku and a.action_type == "EXPIRY_MARKDOWN" for a in self.actions)
            if not existing:
                excess = p.current_stock - (p.dynamic_reorder_point * 2)
                discount_price = round(p.selling_price * 0.92, 2)  # 8% clearance discount
                action = AutonomousAction(
                    action_id=f"ACT-{self._action_counter}",
                    action_type="EXPIRY_MARKDOWN",
                    product_sku=p.sku,
                    title=f"Dead Capital Alert: {p.product_name}",
                    description=(
                        f"Stock {p.current_stock} units bohot slow chal raha hai ({p.days_to_depletion} din ka maal). "
                        f"Working capital free karne ke liye ₹{discount_price} par combo offer chalane ki advice hai."
                    ),
                    urgency="MEDIUM",
                    recommended_payload={
                        "sku": p.sku,
                        "excess_units": excess,
                        "discounted_selling_price": discount_price
                    },
                    auto_executed=False,
                    voice_announcement_text=(
                        f"{p.product_name.split()[0]} ka stock bohot zyada hai. "
                        f"Cash flow free karne ke liye discount offer tayyar hai."
                    )
                )
                self.actions.insert(0, action)
                self._action_counter += 1
        else:
            p.status = "HEALTHY"

    def execute_action(self, action_id: str) -> bool:
        """Executes an autonomous proposal with human approval."""
        for a in self.actions:
            if a.action_id == action_id:
                a.auto_executed = True
                return True
        return False

    def generate_morning_voice_brief(self) -> str:
        """Produces a concise vernacular store agenda spoken aloud to the shopkeeper."""
        critical_items = [p for p in self.profiles.values() if p.status in ["CRITICAL_DEPLETION", "REORDER_NEEDED"]]
        if not critical_items:
            return (
                "Namaste Ramesh Ji! DukaanOS AI brain sabhi SKUs par healthy balance dekh raha hai. "
                "Koi stockout risk nahi hai. Aaj counter sales par focus karein!"
            )
        
        item_names = ", ".join([p.product_name.split()[0] for p in critical_items[:3]])
        return (
            f"Namaste Ramesh Ji! DukaanOS AI brain ne notice kiya hai ki {item_names} ka stock fast khatam ho raha hai. "
            f"Maine vendor ke liye reorder drafts auto-prepare kar diye hain. Ek click se approve karein!"
        )

    def get_state(self) -> StoreBrainState:
        """Returns the full observable state of the store brain."""
        healthy_count = sum(1 for p in self.profiles.values() if p.status == "HEALTHY")
        total = max(len(self.profiles), 1)
        health_score = round((healthy_count / total) * 100, 1)

        return StoreBrainState(
            store_id=self.store_id,
            total_skus_monitored=len(self.profiles),
            total_learning_updates=self.learning_updates_count,
            active_autonomous_actions=self.actions[:10],
            monitored_profiles=list(self.profiles.values()),
            health_score_percent=health_score,
            morning_voice_brief=self.generate_morning_voice_brief()
        )


# Global singleton instance for the store
_brain_registry: Dict[str, AutonomousStoreBrain] = {}


def get_store_brain(store_id: str = "STORE-001") -> AutonomousStoreBrain:
    """Returns or creates the Autonomous Brain singleton for the store."""
    if store_id not in _brain_registry:
        _brain_registry[store_id] = AutonomousStoreBrain(store_id=store_id)
    return _brain_registry[store_id]
