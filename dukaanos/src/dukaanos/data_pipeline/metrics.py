"""Retail Business Intelligence and Operational Metrics for DukaanOS.

Calculates:
- Revenue, COGS, Gross Profit, and Margins (Daily, Monthly, Annual)
- Category-level sales and profitability breakdowns
- Top 10 revenue drivers vs. Bottom 10 slow-moving / dead capital SKUs
- Payment method distribution (UPI vs Cash vs Khata)
- Stockout impact analysis (unfulfilled units, estimated lost revenue)
- Inventory Ledger Reconciliation (reconstructs stock balance per SKU)
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


class RetailMetricsCalculator:
    """Calculates operational and executive KPIs from clean retail data."""

    def __init__(
        self,
        df_sales: pd.DataFrame,
        df_products: pd.DataFrame,
        df_ledger: pd.DataFrame,
        df_stockouts: pd.DataFrame = None,
    ):
        self.df_sales = df_sales.copy()
        self.df_products = df_products.copy()
        self.df_ledger = df_ledger.copy()
        self.df_stockouts = df_stockouts.copy() if df_stockouts is not None else pd.DataFrame()

        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(self.df_sales["date"]):
            self.df_sales["date"] = pd.to_datetime(self.df_sales["date"])
        if not pd.api.types.is_datetime64_any_dtype(self.df_ledger["date"]):
            self.df_ledger["date"] = pd.to_datetime(self.df_ledger["date"])

    def calculate_executive_summary(self) -> Dict[str, Any]:
        """Calculates top-level business performance metrics."""
        total_revenue = float(self.df_sales["total_revenue"].sum())
        total_cogs = float(self.df_sales["total_cost"].sum())
        gross_profit = float(self.df_sales["gross_profit"].sum())
        overall_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0.0

        total_transactions = len(self.df_sales)
        unique_days = self.df_sales["date"].dt.date.nunique()
        total_units_sold = int(self.df_sales["quantity"].sum())

        avg_daily_revenue = total_revenue / unique_days if unique_days > 0 else 0.0
        avg_daily_profit = gross_profit / unique_days if unique_days > 0 else 0.0
        avg_basket_value = total_revenue / total_transactions if total_transactions > 0 else 0.0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_cogs": round(total_cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "overall_margin_pct": round(overall_margin, 2),
            "total_transactions": total_transactions,
            "total_units_sold": total_units_sold,
            "days_analyzed": unique_days,
            "avg_daily_revenue": round(avg_daily_revenue, 2),
            "avg_daily_profit": round(avg_daily_profit, 2),
            "avg_basket_value": round(avg_basket_value, 2),
        }

    def calculate_category_metrics(self) -> pd.DataFrame:
        """Computes revenue, cost, profit, and margins aggregated by category."""
        grouped = self.df_sales.groupby("category").agg(
            total_revenue=("total_revenue", "sum"),
            total_cost=("total_cost", "sum"),
            gross_profit=("gross_profit", "sum"),
            units_sold=("quantity", "sum"),
            transactions=("sales_id", "count"),
        ).reset_index()

        grouped["margin_pct"] = (grouped["gross_profit"] / grouped["total_revenue"] * 100).round(2)
        total_store_revenue = grouped["total_revenue"].sum()
        grouped["revenue_share_pct"] = (grouped["total_revenue"] / total_store_revenue * 100).round(2)

        return grouped.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)

    def calculate_top_and_slow_products(self, n: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Identifies top N revenue drivers and bottom N slow-moving SKUs."""
        prod_metrics = self.df_sales.groupby(["product_id", "product_name", "category"]).agg(
            total_revenue=("total_revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
            units_sold=("quantity", "sum"),
            days_active=("date", lambda s: s.dt.date.nunique()),
        ).reset_index()

        prod_metrics["margin_pct"] = (prod_metrics["gross_profit"] / prod_metrics["total_revenue"] * 100).round(2)

        top_products = prod_metrics.sort_values(by="total_revenue", ascending=False).head(n).reset_index(drop=True)
        slow_products = prod_metrics.sort_values(by="total_revenue", ascending=True).head(n).reset_index(drop=True)

        return top_products, slow_products

    def calculate_payment_method_distribution(self) -> pd.DataFrame:
        """Analyzes transaction and revenue share across payment methods (UPI, Cash, Khata)."""
        grouped = self.df_sales.groupby("payment_method").agg(
            transactions=("sales_id", "count"),
            total_revenue=("total_revenue", "sum"),
        ).reset_index()

        total_tx = grouped["transactions"].sum()
        total_rev = grouped["total_revenue"].sum()

        grouped["transaction_share_pct"] = (grouped["transactions"] / total_tx * 100).round(2)
        grouped["revenue_share_pct"] = (grouped["total_revenue"] / total_rev * 100).round(2)

        return grouped.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)

    def calculate_stockout_impact(self) -> Dict[str, Any]:
        """Estimates lost revenue and unfulfilled demand from stockout records."""
        if self.df_stockouts.empty:
            return {"stockout_incidents": 0, "unfulfilled_units": 0, "estimated_lost_revenue": 0.0}

        incidents = len(self.df_stockouts)
        unfulfilled_units = int(self.df_stockouts["lost_sales_unfulfilled"].sum())

        # Estimated lost revenue = lost_units * unit_price
        lost_revenue = float((self.df_stockouts["lost_sales_unfulfilled"] * self.df_stockouts["unit_price"]).sum())

        # Top 5 SKUs with most stockouts
        top_stockout_skus = (
            self.df_stockouts.groupby(["product_id", "product_name"])
            .agg(stockouts=("sales_id", "count"), lost_units=("lost_sales_unfulfilled", "sum"))
            .sort_values(by="lost_units", ascending=False)
            .head(5)
            .reset_index()
            .to_dict(orient="records")
        )

        return {
            "stockout_incidents": incidents,
            "unfulfilled_units": unfulfilled_units,
            "estimated_lost_revenue": round(lost_revenue, 2),
            "top_stockout_skus": top_stockout_skus,
        }

    def reconcile_inventory_ledger(self) -> Dict[str, Any]:
        """Reconstructs and verifies inventory balance for every SKU via ledger event math:

        Final Balance = Opening Stock + Purchases - Sales - Damage/Expired
        Flags any mathematical inconsistencies.
        """
        reconciliation_results = []
        discrepancies = 0
        total_holding_value = 0.0

        for sku, group in self.df_ledger.groupby("product_id"):
            sorted_events = group.sort_values(by=["date", "transaction_id"]).reset_index(drop=True)

            opening_row = sorted_events[sorted_events["event_type"] == "OPENING_STOCK"]
            opening_stock = opening_row["quantity_change"].sum() if not opening_row.empty else 0

            purchases = sorted_events[sorted_events["event_type"] == "PURCHASE"]["quantity_change"].sum()
            sales = sorted_events[sorted_events["event_type"] == "SALE"]["quantity_change"].sum()  # negative
            damage = sorted_events[sorted_events["event_type"] == "DAMAGE_EXPIRED"]["quantity_change"].sum()  # negative

            calculated_balance = opening_stock + purchases + sales + damage  # sales & damage are already negative
            last_recorded_balance = sorted_events.iloc[-1]["running_balance"]

            # Cost price lookup
            prod_info = self.df_products[self.df_products["product_id"] == sku]
            cost_price = float(prod_info.iloc[0]["cost_price"]) if not prod_info.empty else 0.0

            holding_value = last_recorded_balance * cost_price
            total_holding_value += holding_value

            is_consistent = (calculated_balance == last_recorded_balance)
            if not is_consistent:
                discrepancies += 1

            reconciliation_results.append({
                "product_id": sku,
                "opening_stock": opening_stock,
                "total_purchased": purchases,
                "total_sold": abs(sales),
                "total_damaged": abs(damage),
                "calculated_balance": calculated_balance,
                "ledger_running_balance": last_recorded_balance,
                "is_consistent": is_consistent,
                "current_holding_value": round(holding_value, 2),
            })

        df_recon = pd.DataFrame(reconciliation_results)

        return {
            "total_skus_checked": len(df_recon),
            "discrepancies_detected": discrepancies,
            "ledger_mathematical_integrity_pct": 100.0 if discrepancies == 0 else round((1 - discrepancies / len(df_recon)) * 100, 2),
            "total_inventory_holding_value": round(total_holding_value, 2),
            "reconciliation_sample": df_recon.head(5).to_dict(orient="records"),
        }

