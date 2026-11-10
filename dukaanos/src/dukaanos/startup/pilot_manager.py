"""Pilot Store Trial Operations and Onboarding Manager."""

from typing import Dict, List, Any
from datetime import datetime


PILOT_STORES = [
    {
        "store_id": "PILOT-01",
        "store_name": "Gupta General Store",
        "owner_name": "Ramesh Gupta",
        "location": "Connaught Place, New Delhi",
        "catalog_size": 500,
        "monthly_turnover_inr": 3200000.0,
        "pre_dukaanos_workflow": "Manual red diary (Bahi-Khata) + phone calls to distributors at 9 PM",
        "trial_status": "ACTIVE_PILOT",
        "trial_duration_days": 60,
    },
    {
        "store_id": "PILOT-02",
        "store_name": "Patel Daily Mart",
        "owner_name": "Suresh Patel",
        "location": "Navrangpura, Ahmedabad",
        "catalog_size": 850,
        "monthly_turnover_inr": 4500000.0,
        "pre_dukaanos_workflow": "Basic single-terminal desktop billing software with zero stock tracking",
        "trial_status": "ACTIVE_PILOT",
        "trial_duration_days": 60,
    },
    {
        "store_id": "PILOT-03",
        "store_name": "Maa Tara Provisions",
        "owner_name": "Debabrata Ghosh",
        "location": "Gariahat, Kolkata",
        "catalog_size": 350,
        "monthly_turnover_inr": 2100000.0,
        "pre_dukaanos_workflow": "Visual inspection of shelves every morning; frequent unexpected stockouts",
        "trial_status": "ACTIVE_PILOT",
        "trial_duration_days": 60,
    },
]


class PilotManager:
    """Manages pilot store lifecycle, feedback, and customer operational onboarding."""

    def __init__(self):
        self.stores = PILOT_STORES.copy()

    def get_pilot_stores(self) -> List[Dict[str, Any]]:
        """Returns metadata for all active pilot stores."""
        return self.stores

    def get_pilot_summary(self) -> Dict[str, Any]:
        """Calculates cohort summary across the 3 pilot sites."""
        total_skus = sum(s["catalog_size"] for s in self.stores)
        total_monthly_turnover = sum(s["monthly_turnover_inr"] for s in self.stores)

        return {
            "active_pilots_count": len(self.stores),
            "total_skus_under_management": total_skus,
            "total_monthly_gross_turnover_inr": total_monthly_turnover,
            "pilot_geographies": ["Delhi NCR", "Gujarat", "West Bengal"],
            "average_trial_duration_days": 60,
        }

