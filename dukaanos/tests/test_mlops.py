"""Automated Test Suite for Phase 5 Production MLOps, Registry, and Drift Monitoring."""

import os
import json
import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from dukaanos.src.dukaanos.mlops.registry import ModelRegistry
from dukaanos.src.dukaanos.mlops.drift import calculate_psi, DriftMonitor
from dukaanos.src.dukaanos.mlops.telemetry import TelemetryMetrics, JSONFormatter


@pytest.fixture(scope="module")
def temp_registry(tmp_path_factory):
    """Sets up an isolated model registry in a temp folder."""
    reg_dir = tmp_path_factory.mktemp("mlops_registry")
    return ModelRegistry(registry_dir=str(reg_dir))


def test_model_registry_lifecycle(temp_registry):
    """Verifies that ML model artifacts serialize, register, and load cleanly."""
    dummy_model = Ridge().fit([[1, 2], [3, 4]], [10, 20])
    metrics = {"WAPE_pct": 26.07, "MAE": 3.08}
    features = ["lag_1", "rolling_mean_7"]

    # Register
    entry = temp_registry.register_model(
        model_obj=dummy_model,
        model_name="test_forecaster",
        version="1.0.0",
        metrics=metrics,
        feature_names=features,
        stage="PRODUCTION",
    )
    assert entry["version"] == "1.0.0"
    assert entry["stage"] == "PRODUCTION"
    assert os.path.exists(entry["artifact_path"])

    # Load production model
    loaded_tuple = temp_registry.load_production_model("test_forecaster")
    assert loaded_tuple is not None
    loaded_model, loaded_meta = loaded_tuple
    assert loaded_meta["version"] == "1.0.0"
    assert loaded_meta["metrics"]["WAPE_pct"] == 26.07


def test_psi_stable_distribution():
    """Identical distributions should exhibit negligible PSI (< 0.10)."""
    np.random.seed(42)
    expected = np.random.normal(loc=50.0, scale=10.0, size=1000)
    actual = np.random.normal(loc=50.5, scale=9.8, size=1000)

    psi = calculate_psi(expected, actual)
    assert psi < 0.10, f"Expected stable PSI < 0.10, got {psi}"


def test_psi_drift_detection():
    """Significantly shifted distribution should trigger severe drift (PSI >= 0.25)."""
    np.random.seed(42)
    expected = np.random.normal(loc=20.0, scale=5.0, size=1000)
    # Severe shift: distribution center shifts by 5 standard deviations
    actual_drifted = np.random.normal(loc=45.0, scale=12.0, size=1000)

    psi = calculate_psi(expected, actual_drifted)
    assert psi >= 0.25, f"Expected severe drift PSI >= 0.25, got {psi}"


def test_model_performance_degradation():
    """Verifies that an error spike triggers an automated retraining alert."""
    df_dummy = pd.DataFrame({"units_sold": [10, 20, 30]})
    monitor = DriftMonitor(df_dummy)

    # Baseline WAPE 26%, production degrades to 38%
    alert = monitor.evaluate_model_degradation(baseline_wape=26.07, current_wape=38.5)
    assert alert["status"] == "ALERT_MODEL_DEGRADED"
    assert alert["action_required"] == "TRIGGER_AUTOMATED_RETRAINING"
    assert alert["error_increase_pct"] > 25.0


def test_telemetry_metrics_tracking():
    """Verifies operational counter increments and latency summaries."""
    telemetry = TelemetryMetrics()
    telemetry.increment("sales_transactions_processed", delta=5)
    telemetry.record_latency("forecasting_inference_ms", duration_ms=45.2)
    telemetry.record_latency("forecasting_inference_ms", duration_ms=52.8)

    summary = telemetry.get_summary()
    assert summary["counters"]["sales_transactions_processed"] == 5
    assert summary["latencies_avg_ms"]["forecasting_inference_ms"] == 49.0

