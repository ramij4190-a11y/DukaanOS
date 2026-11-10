"""Retail Anomaly and Operational Discrepancy Detection.

Detects:
1. Demand Spikes / Drops: Statistical Rolling Z-Score on daily SKU velocity
2. Counter Outliers: Multivariate Isolation Forest on sales transactions
3. Shrinkage Anomalies: Inventory loss events exceeding normal thresholds
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


class RetailAnomalyDetector:
    """Identifies operational and demand outliers across sales and inventory."""

    def __init__(self, df_daily_sku: pd.DataFrame, df_sales: pd.DataFrame):
        self.df_daily = df_daily_sku.copy()
        self.df_sales = df_sales.copy()

    def detect_velocity_anomalies(self, z_threshold: float = 2.5) -> pd.DataFrame:
        """Flags daily SKU sales that deviate significantly from their 14-day rolling mean."""
        df = self.df_daily.sort_values(by=["product_id", "date"]).copy()

        grouped = df.groupby("product_id")["units_sold"]
        df["rolling_mean"] = grouped.transform(lambda s: s.shift(1).rolling(14, min_periods=5).mean())
        df["rolling_std"] = grouped.transform(lambda s: s.shift(1).rolling(14, min_periods=5).std()).fillna(0)

        # Avoid division by zero
        df["z_score"] = np.where(
            df["rolling_std"] > 0,
            (df["units_sold"] - df["rolling_mean"]) / df["rolling_std"],
            0.0,
        )

        anomalies = df[df["z_score"].abs() >= z_threshold].copy()
        anomalies["anomaly_type"] = np.where(anomalies["z_score"] > 0, "SPIKE_SURGE", "VELOCITY_DROP")

        return anomalies[[
            "date", "product_id", "product_name", "category",
            "units_sold", "rolling_mean", "z_score", "anomaly_type"
        ]].sort_values(by="z_score", ascending=False).reset_index(drop=True)

    def detect_transaction_outliers(self, contamination: float = 0.01) -> pd.DataFrame:
        """Uses Isolation Forest to detect unusual counter transactions (e.g. bulk purchases or billing anomalies)."""
        features = ["quantity", "total_revenue", "unit_price"]
        clean_sales = self.df_sales.dropna(subset=features).copy()

        iso = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
        clean_sales["anomaly_flag"] = iso.fit_predict(clean_sales[features])
        # -1 indicates an anomaly
        outliers = clean_sales[clean_sales["anomaly_flag"] == -1].copy()

        return outliers[[
            "sales_id", "date", "product_name", "category",
            "quantity", "total_revenue", "payment_method"
        ]].sort_values(by="total_revenue", ascending=False).reset_index(drop=True)

