"""DukaanOS - Project 001 Runner & Executive Analytics Dashboard.

Executes:
1. Synthetic Retail Dataset Generation (100 SKUs, 5 categories, 365 days)
2. Automated Data Cleaning & ETL Pipeline
3. Business Intelligence & Financial KPI Calculations
4. High-Resolution Visual Analytics Generation
5. Inventory Ledger Reconciliation
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from dukaanos.src.dukaanos.data_pipeline.generator import generate_retail_dataset
from dukaanos.src.dukaanos.data_pipeline.cleaner import RetailDataCleaner
from dukaanos.src.dukaanos.data_pipeline.metrics import RetailMetricsCalculator
from dukaanos.src.dukaanos.analysis.visualizer import RetailVisualizer


def format_currency_inr(val: float) -> str:
    """Formats float into Indian numbering system (Lakhs / Crores)."""
    if abs(val) >= 10000000:
        return f"₹{val / 10000000:.2f} Cr"
    elif abs(val) >= 100000:
        return f"₹{val / 100000:.2f} Lakh"
    return f"₹{val:,.2f}"


def main():
    print("=" * 80)
    print("   DUKAANOS - AI-POWERED RETAIL INTELLIGENCE PLATFORM")
    print("   Project 001: Retail Intelligence Dataset & Analytics Engine")
    print("=" * 80)

    raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    charts_dir = os.path.join(PROJECT_ROOT, "reports", "charts")

    # Step 1: Ensure dataset exists or generate
    raw_sales_file = os.path.join(raw_dir, "sales_raw.csv")
    if not os.path.exists(raw_sales_file):
        print("\n[Phase 1/4] Generating 365-day retail dataset (100 SKUs, Indian Kirana model)...")
        generate_retail_dataset(output_dir=raw_dir)
        print("  ✓ Dataset generated successfully.")
    else:
        print("\n[Phase 1/4] Existing raw dataset found in data/raw/.")

    # Step 2: Clean and Normalize
    print("\n[Phase 2/4] Executing ETL Cleaning Pipeline...")
    cleaner = RetailDataCleaner(raw_dir=raw_dir, processed_dir=processed_dir)
    clean_data = cleaner.run_cleaning_pipeline()
    audit = clean_data["audit_log"]
    print(f"  ✓ Processed {audit['sales']['initial_rows']:,} raw sales transactions.")
    print(f"  ✓ Deduplicated: Removed {audit['sales']['duplicates_removed']:,} duplicate entries.")
    print(f"  ✓ Handled Missing: Imputed {audit['sales']['missing_payments_imputed']:,} null payment fields.")
    print(f"  ✓ Stockouts Logged: Isolated {audit['sales']['stockout_events_logged']:,} unfulfilled demand events.")
    print(f"  ✓ Clean Fulfilled Transactions: {audit['sales']['clean_fulfilled_transactions']:,}")

    # Step 3: Business Intelligence & KPI Computations
    print("\n[Phase 3/4] Calculating Retail Business Intelligence KPIs...")
    calc = RetailMetricsCalculator(
        df_sales=clean_data["sales_clean"],
        df_products=clean_data["products"],
        df_ledger=clean_data["ledger_clean"],
        df_stockouts=clean_data["stockouts"],
    )

    summary = calc.calculate_executive_summary()
    cat_df = calc.calculate_category_metrics()
    top_df, slow_df = calc.calculate_top_and_slow_products(n=5)
    pay_df = calc.calculate_payment_method_distribution()
    stockout_info = calc.calculate_stockout_impact()
    ledger_recon = calc.reconcile_inventory_ledger()

    print("\n" + "-" * 80)
    print("                    ANNUAL EXECUTIVE SCORECARD (2025)")
    print("-" * 80)
    print(f"  Total Store Revenue:         {format_currency_inr(summary['total_revenue'])} ({summary['total_revenue']:,.2f})")
    print(f"  Cost of Goods Sold (COGS):   {format_currency_inr(summary['total_cogs'])}")
    print(f"  Gross Profit:                {format_currency_inr(summary['gross_profit'])}")
    print(f"  Overall Gross Margin:        {summary['overall_margin_pct']}%")
    print(f"  Average Daily Revenue:       ₹{summary['avg_daily_revenue']:,.2f}")
    print(f"  Average Daily Gross Profit:  ₹{summary['avg_daily_profit']:,.2f}")
    print(f"  Average Basket Value:        ₹{summary['avg_basket_value']:.2f}")
    print(f"  Current Inventory Value:     {format_currency_inr(ledger_recon['total_inventory_holding_value'])}")
    print(f"  Estimated Stockout Loss:     {format_currency_inr(stockout_info['estimated_lost_revenue'])} ({stockout_info['unfulfilled_units']:,} units)")

    print("\n" + "-" * 80)
    print("                   CATEGORY PERFORMANCE BREAKDOWN")
    print("-" * 80)
    print(f"  {'Category':<28} | {'Revenue':<14} | {'Margin %':<8} | {'Units Sold':<10}")
    print("  " + "-" * 70)
    for _, row in cat_df.iterrows():
        print(f"  {row['category']:<28} | {format_currency_inr(row['total_revenue']):<14} | {row['margin_pct']:>6.1f}% | {int(row['units_sold']):>10,}")

    print("\n" + "-" * 80)
    print("                      TOP 5 REVENUE DRIVERS")
    print("-" * 80)
    for idx, row in top_df.iterrows():
        print(f"  {idx+1}. {row['product_name']:<40} : {format_currency_inr(row['total_revenue'])} ({row['units_sold']:,} units, margin {row['margin_pct']}%)")

    print("\n" + "-" * 80)
    print("                   BOTTOM 5 SLOW-MOVING PRODUCTS")
    print("-" * 80)
    for idx, row in slow_df.iterrows():
        print(f"  {idx+1}. {row['product_name']:<40} : {format_currency_inr(row['total_revenue'])} ({row['units_sold']:,} units, margin {row['margin_pct']}%)")

    print("\n" + "-" * 80)
    print("                     PAYMENT METHOD MIX")
    print("-" * 80)
    for _, row in pay_df.iterrows():
        print(f"  {row['payment_method']:<15} : {format_currency_inr(row['total_revenue']):<12} ({row['revenue_share_pct']}% of revenue, {row['transaction_share_pct']}% of orders)")

    print("\n" + "-" * 80)
    print("               INVENTORY LEDGER RECONCILIATION AUDIT")
    print("-" * 80)
    print(f"  Total SKUs Audited:            {ledger_recon['total_skus_checked']}")
    print(f"  Mathematical Discrepancies:    {ledger_recon['discrepancies_detected']}")
    print(f"  Ledger Integrity Score:        {ledger_recon['ledger_mathematical_integrity_pct']}%")

    # Step 4: Visualizations
    print("\n[Phase 4/4] Generating Publication Charts in reports/charts/...")
    viz = RetailVisualizer(charts_dir=charts_dir)
    chart1 = viz.plot_daily_sales_trend(clean_data["sales_clean"])
    chart2 = viz.plot_category_performance(cat_df)
    chart3 = viz.plot_top_vs_slow_products(top_df, slow_df)
    chart4 = viz.plot_payment_methods(pay_df)
    chart5 = viz.plot_sku_ledger_trace(clean_data["ledger_clean"], sku="STP-001", sku_name="Aashirvaad Atta 5kg", min_reorder=25)

    print(f"  ✓ {os.path.basename(chart1)}")
    print(f"  ✓ {os.path.basename(chart2)}")
    print(f"  ✓ {os.path.basename(chart3)}")
    print(f"  ✓ {os.path.basename(chart4)}")
    print(f"  ✓ {os.path.basename(chart5)}")

    print("\n" + "=" * 80)
    print("   ✓ PROJECT 001 EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()

