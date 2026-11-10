"""Automated Unit and Integration Tests for DukaanOS Retail Pipeline."""

import os
import pytest
import pandas as pd
from dukaanos.src.dukaanos.data_pipeline.generator import generate_retail_dataset
from dukaanos.src.dukaanos.data_pipeline.cleaner import RetailDataCleaner
from dukaanos.src.dukaanos.data_pipeline.metrics import RetailMetricsCalculator


@pytest.fixture(scope="module")
def setup_retail_data(tmp_path_factory):
    """Generates synthetic dataset in a temp directory for fast, isolated testing."""
    test_dir = tmp_path_factory.mktemp("retail_test_data")
    raw_dir = os.path.join(test_dir, "raw")
    processed_dir = os.path.join(test_dir, "processed")

    # Generate small 30-day simulation for swift unit testing
    datasets = generate_retail_dataset(days=30, seed=123, output_dir=raw_dir)

    cleaner = RetailDataCleaner(raw_dir=raw_dir, processed_dir=processed_dir)
    clean_results = cleaner.run_cleaning_pipeline()

    return {
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
        "clean_results": clean_results,
    }


def test_product_catalog_structure(setup_retail_data):
    """Verifies that 100 products exist across exactly 5 categories."""
    df_products = setup_retail_data["clean_results"]["products"]
    assert len(df_products) == 100
    categories = df_products["category"].unique()
    assert len(categories) == 5
    assert "Staples & Grains" in categories
    assert "Edible Oils & Ghee" in categories
    assert "Packaged Foods & Snacks" in categories
    assert "Personal & Home Care" in categories
    assert "Dairy & Fresh Essentials" in categories


def test_sales_deduplication(setup_retail_data):
    """Verifies that duplicate sales IDs are completely eliminated in clean data."""
    df_sales_clean = setup_retail_data["clean_results"]["sales_clean"]
    assert df_sales_clean["sales_id"].duplicated().sum() == 0


def test_missing_value_imputation(setup_retail_data):
    """Verifies that null payment_methods are imputed."""
    df_sales_clean = setup_retail_data["clean_results"]["sales_clean"]
    assert df_sales_clean["payment_method"].isna().sum() == 0


def test_gross_profit_mathematical_integrity(setup_retail_data):
    """Verifies Gross Profit = Total Revenue - Total Cost for every transaction."""
    df_sales = setup_retail_data["clean_results"]["sales_clean"]
    expected_profit = (df_sales["total_revenue"] - df_sales["total_cost"]).round(2)
    actual_profit = df_sales["gross_profit"].round(2)
    diff = (expected_profit - actual_profit).abs().max()
    assert diff < 0.05, f"Maximum difference was {diff}"


def test_inventory_ledger_conservation(setup_retail_data):
    """Verifies that the inventory ledger mathematically reconstructs current stock."""
    df_sales = setup_retail_data["clean_results"]["sales_clean"]
    df_products = setup_retail_data["clean_results"]["products"]
    df_ledger = setup_retail_data["clean_results"]["ledger_clean"]
    df_stockouts = setup_retail_data["clean_results"]["stockouts"]

    calc = RetailMetricsCalculator(df_sales, df_products, df_ledger, df_stockouts)
    recon = calc.reconcile_inventory_ledger()

    assert recon["discrepancies_detected"] == 0
    assert recon["ledger_mathematical_integrity_pct"] == 100.0

