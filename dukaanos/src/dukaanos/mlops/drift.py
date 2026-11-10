"""Data Drift and Model Degradation Monitoring for Production ML.

Implements:
1. Population Stability Index (PSI) for tabular feature distribution shifts
2. Kolmogorov-Smirnov (KS-test) statistical distribution checks
3. Rolling WAPE degradation and automated retraining alert triggers
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats


def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_bins: int = 10) -> float:
    """Calculates Population Stability Index (PSI) between baseline and production distributions.

    PSI < 0.10: No significant shift (Stable)
    0.10 <= PSI < 0.25: Moderate shift (Warning)
    PSI >= 0.25: Severe shift (Action required - Retrain)
    """
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine quantile bins based on expected training distribution
    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(expected, quantiles)
    # Ensure unique edges
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0

    # Add small margins to include min/max
    bin_edges[0] -= 1e-5
    bin_edges[-1] += 1e-5

    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    # Convert to proportions with small epsilon to prevent log(0) or div/0
    eps = 1e-4
    expected_pct = (expected_counts / len(expected)) + eps
    actual_pct = (actual_counts / len(actual)) + eps

    expected_pct /= np.sum(expected_pct)
    actual_pct /= np.sum(actual_pct)

    # PSI Formula = sum((actual - expected) * ln(actual / expected))
    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(round(psi_val, 4))


class DriftMonitor:
    """Monitors live retail features and predictions for distributional drift."""

    def __init__(self, df_baseline: pd.DataFrame):
        self.df_baseline = df_baseline.copy()

    def check_feature_drift(self, df_production: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
        """Scans all critical numerical features for PSI and KS-test drift."""
        feature_reports = {}
        severe_drift_detected = False

        for col in feature_cols:
            if col not in self.df_baseline.columns or col not in df_production.columns:
                continue

            base_vals = self.df_baseline[col].dropna().values
            prod_vals = df_production[col].dropna().values

            psi = calculate_psi(base_vals, prod_vals)

            # KS test: p-value < 0.05 indicates statistically significant distribution divergence
            ks_stat, ks_pvalue = stats.ks_2samp(base_vals, prod_vals)

            if psi >= 0.25:
                status = "SEVERE_DRIFT"
                severe_drift_detected = True
            elif psi >= 0.10:
                status = "MODERATE_DRIFT"
            else:
                status = "STABLE"

            feature_reports[col] = {
                "PSI": psi,
                "status": status,
                "ks_stat": round(float(ks_stat), 4),
                "ks_pvalue": round(float(ks_pvalue), 4),
            }

        return {
            "timestamp": pd.Timestamp.now().isoformat(),
            "overall_status": "RETRAIN_ALERT" if severe_drift_detected else "HEALTHY",
            "features_scanned": len(feature_reports),
            "feature_reports": feature_reports,
        }

    def evaluate_model_degradation(
        self, baseline_wape: float, current_wape: float, alert_threshold_increase_pct: float = 25.0
    ) -> Dict[str, Any]:
        """Evaluates whether current production prediction accuracy has deteriorated beyond threshold."""
        relative_increase = ((current_wape - baseline_wape) / baseline_wape * 100) if baseline_wape > 0 else 0.0
        is_degraded = relative_increase >= alert_threshold_increase_pct

        return {
            "baseline_wape_pct": round(baseline_wape, 2),
            "current_wape_pct": round(current_wape, 2),
            "error_increase_pct": round(relative_increase, 2),
            "status": "ALERT_MODEL_DEGRADED" if is_degraded else "ACCEPTABLE",
            "action_required": "TRIGGER_AUTOMATED_RETRAINING" if is_degraded else "NONE",
        }

