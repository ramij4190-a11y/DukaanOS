"""Inventory Optimization & Automated Reorder Point (ROP) Engine.

Converts demand forecasts, lead times, and demand variability into:
1. Lead-Time Demand (LTD)
2. Statistical Safety Stock (SS) for target service levels (e.g. 95%)
3. Reorder Point (ROP)
4. Automated Purchase Order Suggestions
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class InventoryOptimizer:
    """Calculates dynamic reorder policies and purchase suggestions based on forecasted demand."""

    # Normal distribution Z-scores for desired service levels
    Z_SCORES = {
        0.90: 1.282,
        0.95: 1.645,
        0.98: 2.054,
        0.99: 2.326,
    }

    def __init__(self, df_products: pd.DataFrame, df_daily_sku: pd.DataFrame, service_level: float = 0.95):
        self.df_products = df_products.copy()
        self.df_daily = df_daily_sku.copy()
        self.service_level = service_level
        self.z_score = self.Z_SCORES.get(service_level, 1.645)

    def calculate_reorder_policies(self, lookback_days: int = 30) -> pd.DataFrame:
        """Calculates dynamic ROP and Safety Stock for all SKUs using recent daily sales history."""
        # Consider the last N days of velocity to capture recent trends
        max_date = self.df_daily["date"].max()
        cutoff_date = max_date - pd.Timedelta(days=lookback_days)
        recent_sales = self.df_daily[self.df_daily["date"] >= cutoff_date]

        # Daily mean and standard deviation of demand per SKU
        stats = recent_sales.groupby("product_id")["units_sold"].agg(
            mean_daily_demand="mean",
            std_daily_demand="std",
        ).reset_index().fillna(0.0)

        # Merge with product catalog
        policies = pd.merge(self.df_products, stats, on="product_id", how="left")
        policies["mean_daily_demand"] = policies["mean_daily_demand"].fillna(1.0)
        policies["std_daily_demand"] = policies["std_daily_demand"].fillna(0.5)

        # Statistical Safety Stock: SS = Z * sqrt(LeadTime * (std_d)^2)
        lead_time = policies["lead_time_days"].astype(float)
        policies["safety_stock"] = np.ceil(
            self.z_score * np.sqrt(lead_time * (policies["std_daily_demand"] ** 2))
        ).astype(int)

        # Lead-Time Demand: LTD = mean_demand * LeadTime
        policies["lead_time_demand"] = np.ceil(policies["mean_daily_demand"] * lead_time).astype(int)

        # Dynamic Reorder Point: ROP = LeadTimeDemand + SafetyStock
        policies["reorder_point"] = policies["lead_time_demand"] + policies["safety_stock"]

        return policies[[
            "product_id", "product_name", "category", "supplier_name",
            "cost_price", "lead_time_days", "mean_daily_demand",
            "safety_stock", "lead_time_demand", "reorder_point"
        ]]

    def generate_purchase_recommendations(
        self, df_current_stock: pd.DataFrame, review_period_days: int = 7
    ) -> pd.DataFrame:
        """Compares current stock with dynamic ROP and generates prioritized PO recommendations."""
        policies = self.calculate_reorder_policies()

        merged = pd.merge(
            policies,
            df_current_stock[["product_id", "current_stock"]],
            on="product_id",
            how="left",
        )
        merged["current_stock"] = merged["current_stock"].fillna(0).astype(int)

        # Reorder trigger condition: current_stock <= reorder_point
        needs_reorder = merged["current_stock"] <= merged["reorder_point"]
        reorder_candidates = merged[needs_reorder].copy()

        # Target Order-Up-To Level = ROP + (mean_demand * review_period)
        target_stock = reorder_candidates["reorder_point"] + np.ceil(
            reorder_candidates["mean_daily_demand"] * review_period_days
        )

        reorder_candidates["suggested_order_qty"] = np.maximum(
            target_stock - reorder_candidates["current_stock"], 5
        ).astype(int)

        reorder_candidates["estimated_cost"] = (
            reorder_candidates["suggested_order_qty"] * reorder_candidates["cost_price"]
        ).round(2)

        # Stockout urgency score: (ROP - current_stock) / ROP
        reorder_candidates["urgency_score"] = (
            (reorder_candidates["reorder_point"] - reorder_candidates["current_stock"])
            / np.maximum(reorder_candidates["reorder_point"], 1)
        ).round(2)

        return reorder_candidates.sort_values(by="urgency_score", ascending=False).reset_index(drop=True)

