"""Demand Forecasting Engine with Walk-Forward Backtesting.

Models Evaluated:
1. Baseline: 7-Day Moving Average
2. Linear: Ridge Regression (with Feature Scaling)
3. Ensemble: Random Forest Regressor
4. Gradient Boosted Trees: LightGBM Regressor

Evaluation Protocol:
- Time-based Rolling-Origin Backtesting (Walk-Forward Validation)
- Metrics: WAPE (Weighted Absolute Percentage Error), MAE, RMSE, Forecast Bias
- Hierarchical cold-start fallback heuristic for brand-new SKUs
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes retail forecasting metrics: WAPE, MAE, RMSE, and Bias %."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    # Clip negative predictions to 0 (cannot sell negative items)
    y_pred = np.maximum(y_pred, 0.0)

    total_actual = float(np.sum(y_true))
    abs_errors = np.abs(y_true - y_pred)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # WAPE is robust to small integers and zero-demand days
    wape = (float(np.sum(abs_errors)) / total_actual * 100) if total_actual > 0 else 0.0

    # Forecast bias: positive means over-forecasting, negative means under-forecasting
    bias = (float(np.sum(y_pred - y_true)) / total_actual * 100) if total_actual > 0 else 0.0

    return {
        "WAPE_pct": round(wape, 2),
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "Bias_pct": round(bias, 2),
    }


class DemandForecaster:
    """Manages model training, prediction, and walk-forward cross-validation."""

    FEATURE_COLS = [
        "day_of_week",
        "day_of_month",
        "month",
        "is_weekend",
        "is_salary_week",
        "is_festival",
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_21",
        "rolling_mean_7",
        "rolling_std_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "cost_price",
        "selling_price",
        "category_daily_mean",
    ]

    def __init__(self, df_features: pd.DataFrame):
        self.df = df_features.sort_values(by="date").reset_index(drop=True)
        # Category median lookup for cold-start fallback
        self.category_velocity_median = (
            self.df.groupby("category")["units_sold"].median().to_dict()
        )

    def cold_start_prediction(
        self, category: str, is_weekend: bool = False, is_salary_week: bool = False, is_festival: bool = False
    ) -> float:
        """Hierarchical cold-start fallback heuristic for brand-new SKUs without history."""
        base_median = self.category_velocity_median.get(category, 5.0)
        mult = 1.0
        if is_weekend:
            mult *= 1.35
        if is_salary_week:
            mult *= 1.25
        if is_festival:
            mult *= 1.8
        return round(base_median * mult, 1)

    def run_walk_forward_backtest(
        self, test_window_days: int = 14, num_folds: int = 3
    ) -> Dict[str, Any]:
        """Executes strictly chronological Rolling-Origin Backtesting across all models."""
        max_date = self.df["date"].max()

        results_by_model = {
            "Naive_7D_MovingAvg": [],
            "Ridge_Regression": [],
            "Random_Forest": [],
            "LightGBM": [],
        }

        fold_dates = []
        for fold in range(num_folds, 0, -1):
            test_end = max_date - pd.Timedelta(days=(fold - 1) * test_window_days)
            test_start = test_end - pd.Timedelta(days=test_window_days - 1)
            train_end = test_start - pd.Timedelta(days=1)

            fold_dates.append((train_end.strftime("%Y-%m-%d"), test_start.strftime("%Y-%m-%d"), test_end.strftime("%Y-%m-%d")))

            df_train = self.df[self.df["date"] <= train_end]
            df_test = self.df[(self.df["date"] >= test_start) & (self.df["date"] <= test_end)]

            X_train = df_train[self.FEATURE_COLS].fillna(0)
            y_train = df_train["units_sold"].values
            X_test = df_test[self.FEATURE_COLS].fillna(0)
            y_test = df_test["units_sold"].values

            # 1. Baseline Model: Naive 7-day moving average (already computed in rolling_mean_7)
            y_pred_naive = df_test["rolling_mean_7"].values
            results_by_model["Naive_7D_MovingAvg"].append(compute_metrics(y_test, y_pred_naive))

            # 2. Ridge Regression
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            ridge = Ridge(alpha=10.0)
            ridge.fit(X_train_scaled, y_train)
            y_pred_ridge = ridge.predict(X_test_scaled)
            results_by_model["Ridge_Regression"].append(compute_metrics(y_test, y_pred_ridge))

            # 3. Random Forest Regressor
            rf = RandomForestRegressor(n_estimators=60, max_depth=10, random_state=42, n_jobs=-1)
            rf.fit(X_train, y_train)
            y_pred_rf = rf.predict(X_test)
            results_by_model["Random_Forest"].append(compute_metrics(y_test, y_pred_rf))

            # 4. LightGBM Regressor
            lgb_model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.08,
                random_state=42,
                verbose=-1,
                n_jobs=-1,
            )
            lgb_model.fit(X_train, y_train)
            y_pred_lgb = lgb_model.predict(X_test)
            results_by_model["LightGBM"].append(compute_metrics(y_test, y_pred_lgb))

        # Aggregate metrics across folds
        summary = {}
        for model_name, fold_metrics in results_by_model.items():
            avg_wape = np.mean([m["WAPE_pct"] for m in fold_metrics])
            avg_mae = np.mean([m["MAE"] for m in fold_metrics])
            avg_rmse = np.mean([m["RMSE"] for m in fold_metrics])
            avg_bias = np.mean([m["Bias_pct"] for m in fold_metrics])

            summary[model_name] = {
                "avg_WAPE_pct": round(float(avg_wape), 2),
                "avg_MAE": round(float(avg_mae), 2),
                "avg_RMSE": round(float(avg_rmse), 2),
                "avg_Bias_pct": round(float(avg_bias), 2),
                "fold_details": fold_metrics,
            }

        return {
            "folds": fold_dates,
            "models_summary": summary,
        }

