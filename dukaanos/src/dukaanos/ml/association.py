"""Market Basket Association & Cross-Selling Engine for Retail Assortment.

Calculates:
- Co-purchase frequency across multi-item transactions
- Association metrics: Support, Confidence, and Lift
- Identifies bundling and cross-merchandising opportunities for Kirana stores
"""

from typing import List, Dict, Any
from itertools import combinations
import pandas as pd


class MarketBasketAnalyzer:
    """Discovers frequently co-purchased item pairs from transaction logs."""

    def __init__(self, df_sales: pd.DataFrame):
        self.df_sales = df_sales.copy()

    def find_association_rules(self, min_support_count: int = 20, min_lift: float = 1.1) -> pd.DataFrame:
        """Finds product pairs frequently bought together under the same invoice_id."""
        # 1. Group products by invoice
        basket_series = self.df_sales.groupby("invoice_id")["product_name"].apply(set)
        # Filter for baskets with at least 2 distinct products
        multi_item_baskets = [basket for basket in basket_series if len(basket) >= 2]
        total_baskets = len(basket_series)

        if total_baskets == 0 or len(multi_item_baskets) == 0:
            return pd.DataFrame()

        # 2. Count individual item frequencies
        item_counts: Dict[str, int] = {}
        for basket in multi_item_baskets:
            for item in basket:
                item_counts[item] = item_counts.get(item, 0) + 1

        # 3. Count co-occurrences of pairs
        pair_counts: Dict[tuple, int] = {}
        for basket in multi_item_baskets:
            # Sort items to keep (A, B) unique
            for item_a, item_b in combinations(sorted(basket), 2):
                pair_counts[(item_a, item_b)] = pair_counts.get((item_a, item_b), 0) + 1

        # 4. Compute Support, Confidence, and Lift
        rules = []
        for (item_a, item_b), pair_freq in pair_counts.items():
            if pair_freq < min_support_count:
                continue

            support_ab = pair_freq / total_baskets
            p_a = item_counts[item_a] / total_baskets
            p_b = item_counts[item_b] / total_baskets

            confidence_a_to_b = pair_freq / item_counts[item_a]
            confidence_b_to_a = pair_freq / item_counts[item_b]

            lift = support_ab / (p_a * p_b) if (p_a * p_b) > 0 else 0.0

            if lift >= min_lift:
                rules.append({
                    "product_a": item_a,
                    "product_b": item_b,
                    "co_occurrence_count": pair_freq,
                    "support_pct": round(support_ab * 100, 3),
                    "confidence_a_to_b_pct": round(confidence_a_to_b * 100, 2),
                    "confidence_b_to_a_pct": round(confidence_b_to_a * 100, 2),
                    "lift": round(lift, 2),
                })

        df_rules = pd.DataFrame(rules)
        if not df_rules.empty:
            df_rules = df_rules.sort_values(by="lift", ascending=False).reset_index(drop=True)

        return df_rules

