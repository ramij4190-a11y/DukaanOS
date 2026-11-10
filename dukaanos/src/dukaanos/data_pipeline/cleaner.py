"""Data Cleaning and Normalization Pipeline for DukaanOS.

Handles:
- Identification and removal of duplicate records
- Handling and imputation of missing/null fields
- Type casting, datetime standardization, and schema verification
- Partitioning fulfilled transactions and stockout logs
- Audit reporting of data quality issues
"""

import os
from typing import Dict, Tuple
import pandas as pd
import numpy as np


class RetailDataCleaner:
    """Cleans and standardizes raw retail data for downstream analysis and ML."""

    def __init__(self, raw_dir: str = "dukaanos/data/raw", processed_dir: str = "dukaanos/data/processed"):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        os.makedirs(self.processed_dir, exist_ok=True)
        self.audit_log: Dict[str, any] = {}

    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads raw CSV files from data/raw/."""
        df_products = pd.read_csv(os.path.join(self.raw_dir, "products.csv"))
        df_sales = pd.read_csv(os.path.join(self.raw_dir, "sales_raw.csv"))
        df_ledger = pd.read_csv(os.path.join(self.raw_dir, "inventory_ledger.csv"))
        df_po = pd.read_csv(os.path.join(self.raw_dir, "purchase_orders.csv"))
        return df_products, df_sales, df_ledger, df_po

    def clean_sales(self, df_sales: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cleans sales records, separates fulfilled sales from stockout events.

        Returns: (df_sales_clean, df_stockouts)
        """
        initial_count = len(df_sales)

        # 1. Deduplication
        # A true duplicate has exact same sales_id
        duplicates_removed = df_sales.duplicated(subset=["sales_id"]).sum()
        df_cleaned = df_sales.drop_duplicates(subset=["sales_id"]).copy()

        # 2. Date parsing
        df_cleaned["date"] = pd.to_datetime(df_cleaned["date"])

        # 3. Handle missing values
        missing_payment_count = df_cleaned["payment_method"].isna().sum()
        df_cleaned["payment_method"] = df_cleaned["payment_method"].fillna("CASH")

        # 4. Separate fulfilled sales from unfulfilled stockout signals
        is_stockout = df_cleaned["quantity"] == 0
        df_stockouts = df_cleaned[is_stockout].copy()
        df_sales_clean = df_cleaned[~is_stockout].copy()

        # 5. Type validations
        df_sales_clean["quantity"] = df_sales_clean["quantity"].astype(int)
        df_sales_clean["total_revenue"] = df_sales_clean["total_revenue"].astype(float)
        df_sales_clean["total_cost"] = df_sales_clean["total_cost"].astype(float)
        df_sales_clean["gross_profit"] = df_sales_clean["gross_profit"].astype(float)

        self.audit_log["sales"] = {
            "initial_rows": initial_count,
            "duplicates_removed": int(duplicates_removed),
            "missing_payments_imputed": int(missing_payment_count),
            "stockout_events_logged": int(len(df_stockouts)),
            "clean_fulfilled_transactions": int(len(df_sales_clean)),
        }

        return df_sales_clean, df_stockouts

    def clean_ledger(self, df_ledger: pd.DataFrame) -> pd.DataFrame:
        """Validates and cleans inventory ledger transactions."""
        initial_count = len(df_ledger)

        # 1. Deduplication
        df_cleaned = df_ledger.drop_duplicates(subset=["transaction_id"]).copy()
        dups_removed = initial_count - len(df_cleaned)

        # 2. Date parsing and sorting chronologically
        df_cleaned["date"] = pd.to_datetime(df_cleaned["date"])
        df_cleaned = df_cleaned.sort_values(by=["date", "transaction_id"]).reset_index(drop=True)

        # 3. Data type assurance
        df_cleaned["quantity_change"] = df_cleaned["quantity_change"].astype(int)
        df_cleaned["running_balance"] = df_cleaned["running_balance"].astype(int)

        self.audit_log["ledger"] = {
            "initial_rows": initial_count,
            "duplicates_removed": int(dups_removed),
            "clean_ledger_records": int(len(df_cleaned)),
        }

        return df_cleaned

    def run_cleaning_pipeline(self) -> Dict[str, pd.DataFrame]:
        """Executes full ETL cleaning pipeline and persists clean data to disk."""
        df_products, df_sales_raw, df_ledger_raw, df_po = self.load_raw_data()

        df_sales_clean, df_stockouts = self.clean_sales(df_sales_raw)
        df_ledger_clean = self.clean_ledger(df_ledger_raw)

        # Purchase orders validation
        df_po["order_date"] = pd.to_datetime(df_po["order_date"])
        df_po["expected_delivery_date"] = pd.to_datetime(df_po["expected_delivery_date"])

        # Persist processed clean datasets
        df_sales_clean.to_csv(os.path.join(self.processed_dir, "sales_clean.csv"), index=False)
        df_stockouts.to_csv(os.path.join(self.processed_dir, "stockouts.csv"), index=False)
        df_ledger_clean.to_csv(os.path.join(self.processed_dir, "ledger_clean.csv"), index=False)
        df_po.to_csv(os.path.join(self.processed_dir, "purchase_orders_clean.csv"), index=False)
        df_products.to_csv(os.path.join(self.processed_dir, "products_clean.csv"), index=False)

        return {
            "products": df_products,
            "sales_clean": df_sales_clean,
            "stockouts": df_stockouts,
            "ledger_clean": df_ledger_clean,
            "purchase_orders": df_po,
            "audit_log": self.audit_log,
        }


if __name__ == "__main__":
    cleaner = RetailDataCleaner()
    results = cleaner.run_cleaning_pipeline()
    print("ETL Cleaning Finished Successfully!")
    print("Audit Log Summary:")
    for category, stats in results["audit_log"].items():
        print(f"  [{category}]: {stats}")

