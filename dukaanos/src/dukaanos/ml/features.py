"""Feature Engineering Pipeline for Retail Time-Series Demand Forecasting.

Transforms raw transaction logs into predictive tabular features:
- Complete time-series grid (date x SKU) with explicit 0-demand days
- Calendar and retail cycle indicators (weekends, salary weeks, festivals)
- Autoregressive lag features (lag_1, lag_7, lag_14, lag_21)
- Rolling window statistics with strictly ZERO lookahead bias (shift=1)
"""

from datetime import date
from typing import List, Tuple
import pandas as pd
import numpy as np


# Indian retail festival calendar
FESTIVAL_DATES = {
    pd.to_datetime("2025-03-13"),
    pd.to_datetime("2025-03-14"),  # Holi
    pd.to_datetime("2025-03-30"),
    pd.to_datetime("2025-03-31"),  # Eid
    pd.to_datetime("2025-08-15"),  # Independence Day
    pd.to_datetime("2025-10-18"),
    pd.to_datetime("2025-10-19"),  # Dhanteras
    pd.to_datetime("2025-10-20"),  # Diwali
    pd.to_datetime("2025-10-21"),  # Diwali
    pd.to_datetime("2025-12-31"),  # New Year Eve
}


class RetailFeatureEngineer:
    """Builds lag, rolling, and calendar features for SKU demand modeling."""

    def __init__(self, df_sales: pd.DataFrame, df_products: pd.DataFrame):
        self.df_sales = df_sales.copy()
        self.df_products = df_products.copy()

        if not pd.api.types.is_datetime64_any_dtype(self.df_sales["date"]):
            self.df_sales["date"] = pd.to_datetime(self.df_sales["date"])

    def create_complete_grid(self) -> pd.DataFrame:
        """Constructs an exhaustive (date x SKU) grid ensuring zero-sales days are explicitly recorded as 0."""
        # 1. Daily aggregation per SKU
        daily_sku = (
            self.df_sales.groupby(["date", "product_id"])
            .agg(units_sold=("quantity", "sum"), daily_revenue=("total_revenue", "sum"))
            .reset_index()
        )

        all_dates = pd.date_range(
            start=self.df_sales["date"].min(),
            end=self.df_sales["date"].max(),
            freq="D",
        )
        all_skus = self.df_products["product_id"].unique()

        grid_index = pd.MultiIndex.from_product([all_dates, all_skus], names=["date", "product_id"])
        df_grid = pd.DataFrame(index=grid_index).reset_index()

        # Merge with actual daily sales; fill unrecorded days with 0
        df_merged = pd.merge(df_grid, daily_sku, on=["date", "product_id"], how="left")
        df_merged["units_sold"] = df_merged["units_sold"].fillna(0).astype(int)
        df_merged["daily_revenue"] = df_merged["daily_revenue"].fillna(0.0)

        # Merge product master metadata
        prod_meta = self.df_products[
            ["product_id", "product_name", "category", "cost_price", "selling_price", "min_reorder_level", "lead_time_days"]
        ]
        df_merged = pd.merge(df_merged, prod_meta, on="product_id", how="left")

        return df_merged.sort_values(by=["product_id", "date"]).reset_index(drop=True)

    def extract_features(self, df_grid: pd.DataFrame) -> pd.DataFrame:
        """Computes calendar, lag, and rolling window features for every product."""
        df = df_grid.copy()

        # 1. Calendar & Cycle features
        df["day_of_week"] = df["date"].dt.day_of_week  # 0=Mon, 6=Sun
        df["day_of_month"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["is_salary_week"] = (df["day_of_month"] <= 7).astype(int)
        df["is_festival"] = df["date"].isin(FESTIVAL_DATES).astype(int)

        # 2. Autoregressive Lags (per product)
        # Note: Must group by product_id to prevent cross-SKU leakage
        grouped = df.groupby("product_id")["units_sold"]

        df["lag_1"] = grouped.shift(1)
        df["lag_7"] = grouped.shift(7)
        df["lag_14"] = grouped.shift(14)
        df["lag_21"] = grouped.shift(21)

        # 3. Rolling Statistics (Strictly shifted by 1 day to prevent lookahead bias)
        # Shift(1) ensures we only look at information available at t-1 when predicting t
        df["rolling_mean_7"] = grouped.apply(lambda s: s.shift(1).rolling(7, min_periods=1).mean()).reset_index(drop=True)
        df["rolling_std_7"] = grouped.apply(lambda s: s.shift(1).rolling(7, min_periods=1).std()).reset_index(drop=True).fillna(0)
        df["rolling_mean_14"] = grouped.apply(lambda s: s.shift(1).rolling(14, min_periods=1).mean()).reset_index(drop=True)
        df["rolling_mean_30"] = grouped.apply(lambda s: s.shift(1).rolling(30, min_periods=1).mean()).reset_index(drop=True)

        # 4. Category-level mean momentum
        cat_daily_mean = df.groupby(["date", "category"])["units_sold"].transform("mean")
        df["category_daily_mean"] = cat_daily_mean

        # Drop initial warmup rows where any required feature (e.g. lag_21, rolling stats) is NaN
        required_cols = [
            "lag_1", "lag_7", "lag_14", "lag_21",
            "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "rolling_mean_30",
            "category_daily_mean"
        ]
        df_clean_features = df.dropna(subset=required_cols).reset_index(drop=True)

        return df_clean_features

    def build(self) -> pd.DataFrame:
        """Executes end-to-end feature pipeline."""
        grid = self.create_complete_grid()
        features_df = self.extract_features(grid)
        return features_df

