"""Automated Test Suite for Phase 6 Startup Metrics & Pilot ROI."""

import pytest
from dukaanos.src.dukaanos.startup.pilot_manager import PilotManager
from dukaanos.src.dukaanos.startup.business_metrics import RetailBusinessImpactCalculator


def test_pilot_cohort_summary():
    """Verifies pilot store cohort metadata."""
    manager = PilotManager()
    summary = manager.get_pilot_summary()

    assert summary["active_pilots_count"] == 3
    assert summary["total_skus_under_management"] >= 1500
    assert "Delhi NCR" in summary["pilot_geographies"]


def test_business_kpi_improvements():
    """Verifies that before/after metrics exhibit substantial operational improvements."""
    calc = RetailBusinessImpactCalculator()
    scorecard = calc.get_pilot_impact_scorecard()
    kpis = {k["kpi_name"]: k for k in scorecard["kpi_benchmarks"]}

    # Stockout reduction
    stockout_kpi = next(v for k, v in kpis.items() if "Stockout Rate" in k)
    assert stockout_kpi["baseline_before"] == 8.4
    assert stockout_kpi["dukaanos_after"] == 2.1
    assert stockout_kpi["improvement_pct"] <= -70.0

    # Dead capital reduction
    dead_stock_kpi = next(v for k, v in kpis.items() if "Dead / Overstock" in k)
    assert dead_stock_kpi["baseline_before"] > dead_stock_kpi["dukaanos_after"]

    # Reordering time reduction
    time_kpi = next(v for k, v in kpis.items() if "Daily Time Spent" in k)
    assert time_kpi["dukaanos_after"] <= 15.0


def test_financial_roi_calculation():
    """Verifies unit economics and software ROI multiplier."""
    calc = RetailBusinessImpactCalculator()
    scorecard = calc.get_pilot_impact_scorecard()
    roi = scorecard["financial_roi"]

    assert roi["total_monthly_value_created_inr"] > 20000.0
    assert roi["growth_plan_monthly_price_inr"] == 699.0
    assert roi["roi_multiplier"] > 25.0

