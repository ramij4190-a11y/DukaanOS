"""DukaanOS - Phase 2 Machine Learning Engine & Benchmark Runner.

Executes:
1. Feature Engineering (Lags, Rolling stats, Calendar cycles)
2. Time-Series Rolling-Origin Backtesting (Walk-Forward Validation)
3. Model Benchmark Comparison (Naive MA vs Ridge vs RF vs LightGBM)
4. Anomaly Detection (Statistical Z-score & Isolation Forest)
5. Market Basket Association Mining (Support, Confidence, Lift)
6. Dynamic Inventory Optimization & Purchase Recommendations
7. High-Resolution Visual ML Evaluation Charts
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.ml.features import RetailFeatureEngineer
from dukaanos.src.dukaanos.ml.forecasting import DemandForecaster
from dukaanos.src.dukaanos.ml.anomaly import RetailAnomalyDetector
from dukaanos.src.dukaanos.ml.association import MarketBasketAnalyzer
from dukaanos.src.dukaanos.ml.inventory_opt import InventoryOptimizer

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.dpi"] = 150


def main():
    print("=" * 80)
    print("   DUKAANOS - AI-POWERED RETAIL INTELLIGENCE PLATFORM")
    print("   Phase 2: Machine Learning & Retail Intelligence Engine")
    print("=" * 80)

    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    charts_dir = os.path.join(PROJECT_ROOT, "reports", "charts")
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Load Data
    print("\n[Step 1/6] Loading clean historical datasets...")
    df_sales = pd.read_csv(os.path.join(processed_dir, "sales_clean.csv"))
    df_products = pd.read_csv(os.path.join(processed_dir, "products_clean.csv"))
    df_ledger = pd.read_csv(os.path.join(processed_dir, "ledger_clean.csv"))
    print(f"  ✓ Loaded {len(df_sales):,} sales transactions and {len(df_products)} products.")

    # 2. Feature Engineering
    print("\n[Step 2/6] Building retail features with zero lookahead bias...")
    engineer = RetailFeatureEngineer(df_sales=df_sales, df_products=df_products)
    df_features = engineer.build()
    print(f"  ✓ Feature dataset ready: {len(df_features):,} SKU-day observations.")
    print(f"  ✓ Features generated: {list(DemandForecaster.FEATURE_COLS)}")

    # 3. Time-Series Walk-Forward Backtesting
    print("\n[Step 3/6] Running Rolling-Origin Backtesting (Walk-Forward Cross-Validation)...")
    forecaster = DemandForecaster(df_features)
    backtest_results = forecaster.run_walk_forward_backtest(test_window_days=14, num_folds=3)
    summary = backtest_results["models_summary"]

    print("\n" + "-" * 80)
    print("              DEMAND FORECASTING BENCHMARK SCORECARD")
    print("-" * 80)
    print(f"  {'Model Name':<24} | {'WAPE %':<10} | {'MAE (units)':<12} | {'RMSE':<10} | {'Bias %':<8}")
    print("  " + "-" * 72)
    for model_name, metrics in summary.items():
        print(f"  {model_name:<24} | {metrics['avg_WAPE_pct']:>8.2f}% | {metrics['avg_MAE']:>12.2f} | {metrics['avg_RMSE']:>10.2f} | {metrics['avg_Bias_pct']:>7.2f}%")

    # Determine best model
    best_model_name = min(summary.keys(), key=lambda k: summary[k]["avg_WAPE_pct"])
    print(f"\n  ★ Top Performing Model: {best_model_name} (Lowest WAPE: {summary[best_model_name]['avg_WAPE_pct']}%)")

    # 4. Anomaly Detection
    print("\n[Step 4/6] Executing Anomaly & Discrepancy Detection...")
    anomaly_detector = RetailAnomalyDetector(df_daily_sku=df_features, df_sales=df_sales)
    velocity_anomalies = anomaly_detector.detect_velocity_anomalies(z_threshold=3.0)
    counter_outliers = anomaly_detector.detect_transaction_outliers(contamination=0.005)

    print(f"  ✓ Velocity Anomalies Flagged: {len(velocity_anomalies)} events (Z-Score >= 3.0)")
    if not velocity_anomalies.empty:
        print("    Sample Spikes/Drops:")
        for _, row in velocity_anomalies.head(3).iterrows():
            print(f"      - {row['date']}: {row['product_name'][:30]} -> {row['units_sold']} units sold (Z={row['z_score']:.2f}, {row['anomaly_type']})")

    print(f"  ✓ Transaction Outliers Flagged: {len(counter_outliers)} unusual high-value counter receipts.")

    # 5. Market Basket Association Mining
    print("\n[Step 5/6] Mining Market Basket Association Rules (Apriori/Affinity)...")
    basket_miner = MarketBasketAnalyzer(df_sales=df_sales)
    rules_df = basket_miner.find_association_rules(min_support_count=15, min_lift=1.2)
    print(f"  ✓ Discovered {len(rules_df)} high-affinity cross-selling product pairs (Lift >= 1.2).")
    if not rules_df.empty:
        print("\n  Top Cross-Merchandising Product Pairs (Kirana Bundling):")
        for idx, row in rules_df.head(5).iterrows():
            print(f"    {idx+1}. {row['product_a'][:25]} + {row['product_b'][:25]} (Lift: {row['lift']}x, Conf: {row['confidence_a_to_b_pct']}%)")

    # 6. Dynamic Inventory Optimization & Suggested Purchase Orders
    print("\n[Step 6/6] Computing Dynamic Reorder Points (ROP) & Purchase Recommendations...")
    # Get current stock snapshot from latest ledger balance
    latest_stock = (
        df_ledger.sort_values(by=["date", "transaction_id"])
        .groupby("product_id")
        .last()
        .reset_index()[["product_id", "running_balance"]]
        .rename(columns={"running_balance": "current_stock"})
    )

    optimizer = InventoryOptimizer(df_products=df_products, df_daily_sku=df_features, service_level=0.95)
    po_recommendations = optimizer.generate_purchase_recommendations(df_current_stock=latest_stock)

    print(f"  ✓ Evaluated all 100 SKUs against target 95% service level.")
    print(f"  ✓ Generated {len(po_recommendations)} prioritized Purchase Recommendations.")
    if not po_recommendations.empty:
        print("\n  Top 5 Urgent Purchase Order Suggestions:")
        for idx, row in po_recommendations.head(5).iterrows():
            print(f"    {idx+1}. {row['product_name'][:32]:<32} | Stock: {row['current_stock']:>2} | ROP: {row['reorder_point']:>2} | Order: {row['suggested_order_qty']:>2} units | Cost: ₹{row['estimated_cost']:,.0f}")

    # Generate Evaluation Charts
    print("\nGenerating Phase 2 Visual Analytics Charts in reports/charts/...")

    # Chart 1: Model Benchmark Comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    model_labels = [m.replace("_", "\n") for m in summary.keys()]
    wape_vals = [summary[m]["avg_WAPE_pct"] for m in summary.keys()]
    mae_vals = [summary[m]["avg_MAE"] for m in summary.keys()]

    colors = ["#94a3b8", "#60a5fa", "#3b82f6", "#1d4ed8"]
    bars1 = ax1.bar(model_labels, wape_vals, color=colors, alpha=0.85)
    ax1.set_ylabel("WAPE % (Lower is Better)", fontsize=11, fontweight="bold")
    ax1.set_title("Forecast Error Comparison (WAPE %)", fontsize=12, fontweight="bold")
    for b in bars1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2, h + 0.3, f"{h:.1f}%", ha="center", fontsize=10, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6, axis="y")

    bars2 = ax2.bar(model_labels, mae_vals, color=colors, alpha=0.85)
    ax2.set_ylabel("MAE (Units Sold)", fontsize=11, fontweight="bold")
    ax2.set_title("Mean Absolute Error (Units)", fontsize=12, fontweight="bold")
    for b in bars2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2, h + 0.05, f"{h:.2f}", ha="center", fontsize=10, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6, axis="y")

    fig.suptitle("DukaanOS: Walk-Forward Model Evaluation Across 3 Holdout Folds", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    chart1_path = os.path.join(charts_dir, "model_benchmark_comparison.png")
    plt.savefig(chart1_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Chart 2: Top Association Rules by Lift
    if not rules_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        top_rules = rules_df.head(8).sort_values("lift", ascending=True)
        pair_labels = [f"{r['product_a'][:15]} + {r['product_b'][:15]}" for _, r in top_rules.iterrows()]
        bars = ax.barh(pair_labels, top_rules["lift"], color="#059669", alpha=0.85)
        ax.axvline(1.0, color="#dc2626", linestyle="--", linewidth=1.5, label="Baseline Independence (Lift = 1.0)")
        ax.set_xlabel("Lift (Co-purchase multiplier vs. independent)", fontsize=11, fontweight="bold")
        ax.set_title("DukaanOS: Top Market Basket Product Affinities (Kirana Cross-Selling)", fontsize=12, fontweight="bold")
        for b in bars:
            w = b.get_width()
            ax.text(w + 0.02, b.get_y() + b.get_height() / 2, f"{w:.2f}x", va="center", fontsize=9, fontweight="bold")
        ax.legend(loc="lower right")
        ax.grid(True, linestyle=":", alpha=0.5, axis="x")
        plt.tight_layout()
        chart2_path = os.path.join(charts_dir, "market_basket_lift.png")
        plt.savefig(chart2_path, dpi=200, bbox_inches="tight")
        plt.close(fig)

    print(f"  ✓ {os.path.basename(chart1_path)}")
    if not rules_df.empty:
        print(f"  ✓ {os.path.basename(chart2_path)}")

    print("\n" + "=" * 80)
    print("   ✓ PHASE 2 MACHINE LEARNING ENGINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()

