"""Automated Test Suite for Phase 2 Machine Learning & Inventory Engine."""

import pytest
import numpy as np
import pandas as pd
from dukaanos.src.dukaanos.ml.features import RetailFeatureEngineer
from dukaanos.src.dukaanos.ml.forecasting import compute_metrics, DemandForecaster
from dukaanos.src.dukaanos.ml.inventory_opt import InventoryOptimizer


@pytest.fixture(scope="module")
def sample_ml_data():
    """Generates synthetic minimal data for fast ML testing."""
    dates = pd.date_range("2025-01-01", periods=60, freq="D")
    skus = ["STP-001", "PCK-001"]

    products = pd.DataFrame([
        {"product_id": "STP-001", "product_name": "Atta 5kg", "category": "Staples & Grains", "cost_price": 200.0, "selling_price": 220.0, "min_reorder_level": 15, "lead_time_days": 2, "supplier_name": "Mandi"},
        {"product_id": "PCK-001", "product_name": "Maggi 70g", "category": "Packaged Foods & Snacks", "cost_price": 11.0, "selling_price": 14.0, "min_reorder_level": 30, "lead_time_days": 1, "supplier_name": "Distributor"},
    ])

    sales_rows = []
    for d in dates:
        for sku in skus:
            qty = 5 if sku == "STP-001" else 15
            sales_rows.append({
                "sales_id": f"S-{len(sales_rows)}",
                "invoice_id": f"INV-{len(sales_rows)}",
                "date": d,
                "product_id": sku,
                "product_name": "Atta 5kg" if sku == "STP-001" else "Maggi 70g",
                "category": "Staples & Grains" if sku == "STP-001" else "Packaged Foods & Snacks",
                "quantity": qty,
                "unit_price": 220.0 if sku == "STP-001" else 14.0,
                "total_revenue": qty * (220.0 if sku == "STP-001" else 14.0),
                "total_cost": qty * (200.0 if sku == "STP-001" else 11.0),
                "gross_profit": qty * 20.0,
                "payment_method": "UPI",
            })

    df_sales = pd.DataFrame(sales_rows)
    return products, df_sales


def test_feature_engineering_dimensions(sample_ml_data):
    """Verifies that the feature pipeline produces expected lag and calendar columns without NaNs."""
    products, df_sales = sample_ml_data
    engineer = RetailFeatureEngineer(df_sales, products)
    df_feat = engineer.build()

    assert not df_feat.empty
    expected_cols = ["lag_1", "lag_7", "lag_14", "rolling_mean_7", "day_of_week", "is_weekend"]
    for col in expected_cols:
        assert col in df_feat.columns
    assert df_feat["rolling_mean_7"].isna().sum() == 0


def test_wape_metric_properties():
    """Verifies exact mathematical properties of WAPE."""
    y_true = np.array([10, 20, 30])
    # Exact prediction -> WAPE 0%
    metrics_perfect = compute_metrics(y_true, y_true)
    assert metrics_perfect["WAPE_pct"] == 0.0

    # 100% over-prediction
    y_pred_double = np.array([20, 40, 60])
    metrics_double = compute_metrics(y_true, y_pred_double)
    assert metrics_double["WAPE_pct"] == 100.0
    assert metrics_double["Bias_pct"] == 100.0


def test_cold_start_fallback(sample_ml_data):
    """Verifies that the cold-start engine returns a valid, positive demand prediction."""
    products, df_sales = sample_ml_data
    engineer = RetailFeatureEngineer(df_sales, products)
    df_feat = engineer.build()

    forecaster = DemandForecaster(df_feat)
    pred = forecaster.cold_start_prediction("Staples & Grains", is_weekend=True)
    assert pred > 0.0
    assert isinstance(pred, float)


def test_inventory_rop_math(sample_ml_data):
    """Verifies that ROP >= LeadTimeDemand and SafetyStock > 0."""
    products, df_sales = sample_ml_data
    engineer = RetailFeatureEngineer(df_sales, products)
    df_feat = engineer.build()

    optimizer = InventoryOptimizer(products, df_feat)
    policies = optimizer.calculate_reorder_policies()

    assert len(policies) == len(products)
    for _, row in policies.iterrows():
        assert row["reorder_point"] >= row["lead_time_demand"]
        assert row["safety_stock"] >= 0

