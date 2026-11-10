"""Visualization and Retail Intelligence Charting for DukaanOS.

Generates high-resolution publication charts:
1. Daily Sales Trend with 7-day rolling average & festival annotations
2. Category Performance (Revenue vs. Gross Margin %)
3. Top 10 Revenue Generators vs Bottom 10 Slow Movers
4. Payment Methods Distribution (UPI / Cash / Khata)
5. Inventory Ledger Running Balance Trace for representative SKUs
"""

import os
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np

# Styling configuration
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["figure.dpi"] = 150


class RetailVisualizer:
    """Generates visual analytics and charts for retail business reports."""

    def __init__(self, charts_dir: str = "dukaanos/reports/charts"):
        self.charts_dir = charts_dir
        os.makedirs(self.charts_dir, exist_ok=True)

    def plot_daily_sales_trend(self, df_sales: pd.DataFrame, output_name: str = "daily_sales_trend.png") -> str:
        """Plots 365 days of store revenue with 7-day and 30-day moving averages and festival annotations."""
        # Aggregate daily
        daily = df_sales.groupby("date").agg(
            revenue=("total_revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
            transactions=("sales_id", "count"),
        ).reset_index().sort_values("date")

        daily["rev_7d_ma"] = daily["revenue"].rolling(window=7, min_periods=1).mean()
        daily["rev_30d_ma"] = daily["revenue"].rolling(window=30, min_periods=1).mean()

        fig, ax = plt.subplots(figsize=(14, 6))

        # Raw daily scatter / bar
        ax.bar(daily["date"], daily["revenue"], color="#93c5fd", alpha=0.5, label="Daily Revenue (₹)", width=1.0)
        # Moving averages
        ax.plot(daily["date"], daily["rev_7d_ma"], color="#1d4ed8", linewidth=2.0, label="7-Day Moving Avg (Weekly Cycle)")
        ax.plot(daily["date"], daily["rev_30d_ma"], color="#b91c1c", linewidth=2.5, linestyle="--", label="30-Day Trend")

        # Annotations for Indian retail spikes
        diwali_date = pd.to_datetime("2025-10-20")
        if diwali_date in daily["date"].values:
            diwali_rev = daily[daily["date"] == diwali_date]["revenue"].values[0]
            ax.annotate(
                f"Diwali Peak\n₹{diwali_rev:,.0f}",
                xy=(diwali_date, diwali_rev),
                xytext=(diwali_date - pd.Timedelta(days=25), diwali_rev * 0.95),
                arrowprops=dict(facecolor="#b45309", arrowstyle="->", lw=1.5),
                fontsize=9,
                fontweight="bold",
                color="#78350f",
                bbox=dict(boxstyle="round,pad=0.3", fc="#fef3c7", ec="#f59e0b", lw=1),
            )

        holi_date = pd.to_datetime("2025-03-14")
        if holi_date in daily["date"].values:
            holi_rev = daily[daily["date"] == holi_date]["revenue"].values[0]
            ax.annotate(
                f"Holi Surge\n₹{holi_rev:,.0f}",
                xy=(holi_date, holi_rev),
                xytext=(holi_date - pd.Timedelta(days=20), holi_rev * 1.05),
                arrowprops=dict(facecolor="#059669", arrowstyle="->", lw=1.5),
                fontsize=9,
                fontweight="bold",
                color="#065f46",
                bbox=dict(boxstyle="round,pad=0.3", fc="#d1fae5", ec="#10b981", lw=1),
            )

        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.set_ylabel("Revenue (₹)", fontsize=11, fontweight="bold")
        ax.set_title("DukaanOS: 365-Day Daily Store Revenue & Seasonal Dynamics (Kirana Model)", fontsize=14, fontweight="bold", pad=15)
        ax.legend(loc="upper left", frameon=True)
        ax.grid(True, linestyle=":", alpha=0.6)

        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, output_name)
        plt.savefig(output_path, dpi=200)
        plt.close(fig)
        return output_path

    def plot_category_performance(self, df_cat: pd.DataFrame, output_name: str = "category_performance.png") -> str:
        """Plots dual comparison: Category Revenue (in Lakhs) vs. Gross Profit Margin %."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        df_sorted = df_cat.sort_values("total_revenue", ascending=True)

        # 1. Total Revenue (in ₹ Lakhs: 1 Lakh = 100,000)
        rev_lakhs = df_sorted["total_revenue"] / 100000.0
        bars1 = ax1.barh(df_sorted["category"], rev_lakhs, color="#2563eb", alpha=0.85)
        ax1.set_xlabel("Revenue (₹ in Lakhs)", fontsize=11, fontweight="bold")
        ax1.set_title("Total Revenue by Category", fontsize=12, fontweight="bold")
        for bar in bars1:
            w = bar.get_width()
            ax1.text(w + 0.2, bar.get_y() + bar.get_height() / 2, f"₹{w:.2f}L", va="center", fontsize=9, fontweight="bold")
        ax1.grid(True, linestyle=":", alpha=0.5, axis="x")

        # 2. Margin %
        df_margin_sorted = df_cat.sort_values("margin_pct", ascending=True)
        colors = ["#10b981" if m >= 18 else ("#f59e0b" if m >= 10 else "#ef4444") for m in df_margin_sorted["margin_pct"]]
        bars2 = ax2.barh(df_margin_sorted["category"], df_margin_sorted["margin_pct"], color=colors, alpha=0.85)
        ax2.set_xlabel("Gross Profit Margin (%)", fontsize=11, fontweight="bold")
        ax2.set_title("Gross Profit Margin % by Category", fontsize=12, fontweight="bold")
        for bar in bars2:
            w = bar.get_width()
            ax2.text(w + 0.3, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va="center", fontsize=9, fontweight="bold")
        ax2.grid(True, linestyle=":", alpha=0.5, axis="x")

        fig.suptitle("DukaanOS: Category Financial Performance Breakdown", fontsize=14, fontweight="bold", y=1.03)
        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, output_name)
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_top_vs_slow_products(
        self, top_df: pd.DataFrame, slow_df: pd.DataFrame, output_name: str = "top_vs_slow_products.png"
    ) -> str:
        """Plots Top 10 Revenue Drivers vs Bottom 10 Slow-Moving Products."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Top 10
        top_sorted = top_df.sort_values("total_revenue", ascending=True)
        # Shorten product name if too long
        names_top = [n[:28] + "..." if len(n) > 28 else n for n in top_sorted["product_name"]]
        bars1 = ax1.barh(names_top, top_sorted["total_revenue"] / 1000.0, color="#059669", alpha=0.85)
        ax1.set_xlabel("Revenue (₹ Thousands)", fontsize=11, fontweight="bold")
        ax1.set_title("Top 10 Revenue Generators", fontsize=12, fontweight="bold")
        for bar in bars1:
            w = bar.get_width()
            ax1.text(w + 2, bar.get_y() + bar.get_height() / 2, f"₹{w:.1f}k", va="center", fontsize=8, fontweight="bold")
        ax1.grid(True, linestyle=":", alpha=0.5, axis="x")

        # Slow 10
        slow_sorted = slow_df.sort_values("total_revenue", ascending=True)
        names_slow = [n[:28] + "..." if len(n) > 28 else n for n in slow_sorted["product_name"]]
        bars2 = ax2.barh(names_slow, slow_sorted["total_revenue"] / 1000.0, color="#dc2626", alpha=0.85)
        ax2.set_xlabel("Revenue (₹ Thousands)", fontsize=11, fontweight="bold")
        ax2.set_title("Bottom 10 Slow Movers (Dead Capital Risk)", fontsize=12, fontweight="bold")
        for bar in bars2:
            w = bar.get_width()
            ax2.text(w + 0.5, bar.get_y() + bar.get_height() / 2, f"₹{w:.1f}k", va="center", fontsize=8, fontweight="bold")
        ax2.grid(True, linestyle=":", alpha=0.5, axis="x")

        fig.suptitle("DukaanOS: Product Velocity & Assortment Intelligence", fontsize=14, fontweight="bold", y=1.02)
        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, output_name)
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_payment_methods(self, df_pay: pd.DataFrame, output_name: str = "payment_methods.png") -> str:
        """Plots Donut chart of payment mix (UPI vs Cash vs Khata Credit)."""
        fig, ax = plt.subplots(figsize=(7, 7))

        colors = ["#3b82f6", "#10b981", "#f59e0b"]
        wedges, texts, autotexts = ax.pie(
            df_pay["total_revenue"],
            labels=df_pay["payment_method"],
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.75,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        )

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontsize(10)
            autotext.set_weight("bold")

        ax.set_title("Revenue Share by Payment Method\n(Indian Retail Dynamics)", fontsize=13, fontweight="bold", pad=20)
        output_path = os.path.join(self.charts_dir, output_name)
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_sku_ledger_trace(
        self, df_ledger: pd.DataFrame, sku: str = "STP-001", sku_name: str = "Aashirvaad Atta 5kg", min_reorder: int = 25, output_name: str = "inventory_ledger_trace.png"
    ) -> str:
        """Visualizes the exact inventory ledger balance over time for a representative SKU."""
        sku_events = df_ledger[df_ledger["product_id"] == sku].copy()
        if sku_events.empty:
            return ""

        sku_events = sku_events.sort_values(by=["date", "transaction_id"]).reset_index(drop=True)

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.step(sku_events["date"], sku_events["running_balance"], where="post", color="#1e40af", linewidth=1.8, label="Running Stock (Units)")
        ax.axhline(min_reorder, color="#dc2626", linestyle="--", linewidth=1.5, label=f"Reorder Trigger Level ({min_reorder} units)")

        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.set_ylabel("Available Stock (Units)", fontsize=11, fontweight="bold")
        ax.set_title(f"DukaanOS Inventory Ledger Trace: {sku_name} ({sku})", fontsize=13, fontweight="bold", pad=12)
        ax.legend(loc="upper right", frameon=True)
        ax.grid(True, linestyle=":", alpha=0.6)

        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, output_name)
        plt.savefig(output_path, dpi=200)
        plt.close(fig)
        return output_path

