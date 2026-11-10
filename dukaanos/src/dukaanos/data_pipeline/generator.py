"""Realistic Synthetic Retail Dataset Generator for DukaanOS.

Simulates 365 days of Indian grocery / Kirana store operations:
- 100 realistic SKUs across 5 core categories
- Realistic pricing, margins, and supplier lead times
- Day-of-week, monthly salary cycles, and festival demand spikes
- Inventory Ledger with traceable events (OPENING_STOCK, PURCHASE, SALE, DAMAGE)
- Stockouts when stock hits 0
- Deliberate real-world imperfections (duplicates, missing values) for ETL validation
"""

import os
import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


# Product Catalog Blueprint: 100 SKUs across 5 core Indian retail categories
CATALOG_SPECS = [
    # 1. Staples & Grains (20 SKUs) - Margins: 6% - 10%
    ("STP-001", "Aashirvaad Shudh Chakki Atta 5kg", "Staples & Grains", "Bag", 225.0, 245.0, 25, 2, 90, 8),
    ("STP-002", "Fortune Chakki Fresh Atta 10kg", "Staples & Grains", "Bag", 410.0, 445.0, 15, 2, 90, 5),
    ("STP-003", "India Gate Basmati Rice Classic 1kg", "Staples & Grains", "Pouch", 145.0, 165.0, 30, 3, 365, 7),
    ("STP-004", "Daawat Rozana Basmati Rice 5kg", "Staples & Grains", "Bag", 370.0, 410.0, 15, 3, 365, 4),
    ("STP-005", "Loose Sona Masoori Rice 1kg", "Staples & Grains", "kg", 46.0, 52.0, 50, 2, 180, 16),
    ("STP-006", "Tata Sampann Unpolished Toor Dal 1kg", "Staples & Grains", "Pouch", 155.0, 172.0, 25, 3, 180, 9),
    ("STP-007", "Loose Toor Dal Premium 1kg", "Staples & Grains", "kg", 140.0, 155.0, 40, 2, 180, 14),
    ("STP-008", "Tata Sampann Moong Dal 500g", "Staples & Grains", "Pouch", 68.0, 78.0, 20, 3, 180, 6),
    ("STP-009", "Loose Chana Dal 1kg", "Staples & Grains", "kg", 82.0, 92.0, 30, 2, 180, 10),
    ("STP-010", "Loose Kabuli Chana 1kg", "Staples & Grains", "kg", 125.0, 140.0, 20, 2, 180, 5),
    ("STP-011", "Tata Salt Vacuum Evaporated 1kg", "Staples & Grains", "Pouch", 24.0, 28.0, 60, 1, 720, 22),
    ("STP-012", "Tata Salt Lite 1kg", "Staples & Grains", "Pouch", 38.0, 45.0, 15, 2, 720, 4),
    ("STP-013", "Madhur Pure & Hygienic Sugar 1kg", "Staples & Grains", "Pouch", 46.0, 52.0, 35, 2, 720, 12),
    ("STP-014", "Loose Refined Sugar 1kg", "Staples & Grains", "kg", 41.0, 46.0, 80, 1, 720, 25),
    ("STP-015", "Loose Premium Maida 1kg", "Staples & Grains", "kg", 38.0, 44.0, 25, 2, 90, 8),
    ("STP-016", "Loose Premium Sooji / Rava 1kg", "Staples & Grains", "kg", 40.0, 46.0, 25, 2, 90, 7),
    ("STP-017", "Catch Turmeric Powder 200g", "Staples & Grains", "Pouch", 52.0, 62.0, 20, 3, 365, 6),
    ("STP-018", "MDH Deggi Mirch 100g", "Staples & Grains", "Box", 72.0, 84.0, 20, 3, 365, 5),
    ("STP-019", "Everest Coriander Powder 200g", "Staples & Grains", "Pouch", 55.0, 65.0, 20, 3, 365, 6),
    ("STP-020", "Tata Sampann Garam Masala 100g", "Staples & Grains", "Box", 80.0, 94.0, 15, 3, 365, 4),

    # 2. Edible Oils & Ghee (15 SKUs) - Margins: 7% - 12%
    ("OIL-001", "Fortune Kachi Ghani Mustard Oil 1L", "Edible Oils & Ghee", "Bottle", 132.0, 148.0, 30, 2, 270, 14),
    ("OIL-002", "Engine Brand Mustard Oil 1L", "Edible Oils & Ghee", "Bottle", 142.0, 158.0, 25, 2, 270, 10),
    ("OIL-003", "Fortune Sunlite Refined Sunflower Oil 1L", "Edible Oils & Ghee", "Pouch", 118.0, 132.0, 35, 2, 270, 15),
    ("OIL-004", "Saffola Gold Blended Oil 1L", "Edible Oils & Ghee", "Bottle", 152.0, 175.0, 20, 3, 270, 8),
    ("OIL-005", "Gemini Refined Soybean Oil 1L", "Edible Oils & Ghee", "Pouch", 108.0, 122.0, 30, 2, 270, 11),
    ("OIL-006", "Fortune Soyabean Oil 1L Pouch", "Edible Oils & Ghee", "Pouch", 110.0, 124.0, 30, 2, 270, 12),
    ("OIL-007", "Amul Pure Ghee 1L Tin", "Edible Oils & Ghee", "Tin", 585.0, 640.0, 15, 3, 270, 6),
    ("OIL-008", "Amul Pure Ghee 500ml Pouch", "Edible Oils & Ghee", "Pouch", 295.0, 325.0, 20, 3, 270, 7),
    ("OIL-009", "Mother Dairy Pure Ghee 1L Tin", "Edible Oils & Ghee", "Tin", 575.0, 635.0, 12, 3, 270, 5),
    ("OIL-010", "Ananda Pure Cow Ghee 500ml", "Edible Oils & Ghee", "Jar", 310.0, 345.0, 12, 3, 270, 4),
    ("OIL-011", "Patanjali Cow Ghee 1L Pouch", "Edible Oils & Ghee", "Pouch", 560.0, 615.0, 15, 3, 270, 5),
    ("OIL-012", "Dhara Mustard Oil 1L Poly", "Edible Oils & Ghee", "Pouch", 128.0, 142.0, 20, 2, 270, 7),
    ("OIL-013", "Figaro Olive Oil Pure 500ml", "Edible Oils & Ghee", "Tin", 620.0, 715.0, 6, 4, 720, 1),
    ("OIL-014", "Tilsona Sesame Oil 500ml", "Edible Oils & Ghee", "Bottle", 165.0, 188.0, 8, 3, 365, 2),
    ("OIL-015", "Dalda Vanaspati 1L Pouch", "Edible Oils & Ghee", "Pouch", 98.0, 112.0, 15, 2, 180, 4),

    # 3. Packaged Foods & Snacks (25 SKUs) - Margins: 14% - 22%
    ("PCK-001", "Maggi 2-Minute Masala Noodles 70g", "Packaged Foods & Snacks", "Pouch", 11.5, 14.0, 100, 1, 240, 35),
    ("PCK-002", "Maggi Masala Noodles 4-Pack 280g", "Packaged Foods & Snacks", "Pack", 46.0, 56.0, 30, 2, 240, 12),
    ("PCK-003", "Yippee Magic Masala Noodles 65g", "Packaged Foods & Snacks", "Pouch", 10.0, 12.0, 40, 2, 240, 10),
    ("PCK-004", "Parle-G Glucose Biscuits 250g", "Packaged Foods & Snacks", "Pack", 25.0, 30.0, 80, 1, 180, 28),
    ("PCK-005", "Parle-G Gold Biscuits 100g", "Packaged Foods & Snacks", "Pack", 8.2, 10.0, 60, 1, 180, 20),
    ("PCK-006", "Britannia Good Day Butter Cookies 200g", "Packaged Foods & Snacks", "Pack", 38.0, 45.0, 40, 2, 180, 16),
    ("PCK-007", "Britannia Marie Gold Biscuits 300g", "Packaged Foods & Snacks", "Pack", 34.0, 40.0, 50, 2, 180, 18),
    ("PCK-008", "Sunfeast Dark Fantasy Choco Fills 100g", "Packaged Foods & Snacks", "Box", 40.0, 50.0, 25, 2, 180, 7),
    ("PCK-009", "Oreo Original Vanilla Creme 120g", "Packaged Foods & Snacks", "Pack", 31.0, 38.0, 30, 2, 240, 10),
    ("PCK-010", "Lay's India's Magic Masala Chips 50g", "Packaged Foods & Snacks", "Pouch", 16.5, 20.0, 50, 1, 120, 22),
    ("PCK-011", "Lay's Spanish Tomato Tango 50g", "Packaged Foods & Snacks", "Pouch", 16.5, 20.0, 40, 1, 120, 16),
    ("PCK-012", "Kurkure Masala Munch 90g", "Packaged Foods & Snacks", "Pouch", 16.5, 20.0, 50, 1, 120, 24),
    ("PCK-013", "Haldiram's Aloo Bhujia 200g", "Packaged Foods & Snacks", "Pouch", 46.0, 55.0, 35, 2, 180, 14),
    ("PCK-014", "Haldiram's Khatta Meetha Mixture 200g", "Packaged Foods & Snacks", "Pouch", 46.0, 55.0, 30, 2, 180, 12),
    ("PCK-015", "Bikano Bhujia Sev 200g", "Packaged Foods & Snacks", "Pouch", 42.0, 50.0, 25, 2, 180, 8),
    ("PCK-016", "Kissan Fresh Tomato Ketchup 500g", "Packaged Foods & Snacks", "Bottle", 102.0, 125.0, 20, 3, 270, 6),
    ("PCK-017", "Maggi Rich Tomato Ketchup Squeezy 500g", "Packaged Foods & Snacks", "Bottle", 108.0, 130.0, 20, 3, 270, 7),
    ("PCK-018", "Brooke Bond Red Label Tea 500g", "Packaged Foods & Snacks", "Box", 240.0, 280.0, 25, 2, 365, 9),
    ("PCK-019", "Tata Tea Gold 500g", "Packaged Foods & Snacks", "Pouch", 255.0, 295.0, 25, 2, 365, 10),
    ("PCK-020", "Wagh Bakri Premium Leaf Tea 500g", "Packaged Foods & Snacks", "Box", 245.0, 285.0, 15, 2, 365, 5),
    ("PCK-021", "Nescafe Classic Instant Coffee Jar 50g", "Packaged Foods & Snacks", "Jar", 160.0, 190.0, 15, 3, 540, 4),
    ("PCK-022", "Bru Instant Coffee 100g", "Packaged Foods & Snacks", "Pouch", 170.0, 205.0, 15, 3, 540, 5),
    ("PCK-023", "Bournvita Chocolate Health Drink 500g", "Packaged Foods & Snacks", "Jar", 215.0, 250.0, 15, 3, 365, 4),
    ("PCK-024", "Horlicks Classic Malt 500g Refill", "Packaged Foods & Snacks", "Pouch", 220.0, 255.0, 15, 3, 365, 4),
    ("PCK-025", "Kellogg's Corn Flakes Original 500g", "Packaged Foods & Snacks", "Box", 175.0, 210.0, 12, 3, 270, 3),

    # 4. Personal & Home Care (25 SKUs) - Margins: 18% - 28%
    ("PER-001", "Surf Excel Easy Wash Detergent Powder 1kg", "Personal & Home Care", "Pouch", 124.0, 148.0, 30, 2, 720, 12),
    ("PER-002", "Tide Plus Extra Power Detergent 1kg", "Personal & Home Care", "Pouch", 112.0, 134.0, 30, 2, 720, 11),
    ("PER-003", "Ariel Complete Detergent Powder 1kg", "Personal & Home Care", "Pouch", 178.0, 215.0, 15, 3, 720, 5),
    ("PER-004", "Rin Detergent Bar 250g", "Personal & Home Care", "Bar", 16.0, 20.0, 50, 1, 720, 20),
    ("PER-005", "Vim Dishwash Bar 300g Tub", "Personal & Home Care", "Tub", 32.0, 40.0, 40, 2, 720, 15),
    ("PER-006", "Vim Dishwash Liquid Gel Lemon 500ml", "Personal & Home Care", "Bottle", 108.0, 130.0, 20, 2, 720, 7),
    ("PER-007", "Exo Dishwash Touch & Shine Round 500g", "Personal & Home Care", "Tub", 44.0, 55.0, 25, 2, 720, 8),
    ("PER-008", "Dettol Original Bathing Soap 125g (Pack of 3)", "Personal & Home Care", "Multipack", 145.0, 175.0, 25, 2, 720, 9),
    ("PER-009", "Lifebuoy Total Germ Protection Soap 100g", "Personal & Home Care", "Bar", 26.0, 32.0, 40, 2, 720, 14),
    ("PER-010", "Dove Cream Beauty Bathing Bar 100g", "Personal & Home Care", "Bar", 52.0, 65.0, 20, 2, 720, 6),
    ("PER-011", "Lux Velvet Glow Soap 100g", "Personal & Home Care", "Bar", 28.0, 35.0, 30, 2, 720, 10),
    ("PER-012", "Clinic Plus Strong & Long Shampoo 340ml", "Personal & Home Care", "Bottle", 185.0, 225.0, 18, 2, 720, 7),
    ("PER-013", "Head & Shoulders Anti Dandruff Shampoo 180ml", "Personal & Home Care", "Bottle", 160.0, 195.0, 15, 3, 720, 5),
    ("PER-014", "Clinic Plus Shampoo Sachet 6ml (Box of 96)", "Personal & Home Care", "Box", 80.0, 96.0, 25, 2, 720, 18),
    ("PER-015", "Colgate Strong Teeth Toothpaste 200g", "Personal & Home Care", "Tube", 95.0, 118.0, 35, 2, 720, 14),
    ("PER-016", "Close Up Red Hot Gel Toothpaste 150g", "Personal & Home Care", "Tube", 88.0, 110.0, 25, 2, 720, 9),
    ("PER-017", "Sensodyne Fresh Mint Toothpaste 75g", "Personal & Home Care", "Tube", 125.0, 155.0, 15, 3, 720, 4),
    ("PER-018", "Oral-B Shiny Clean Toothbrush Medium", "Personal & Home Care", "Piece", 20.0, 25.0, 40, 2, 1080, 11),
    ("PER-019", "Harpic Power Plus Toilet Cleaner 500ml", "Personal & Home Care", "Bottle", 80.0, 99.0, 30, 2, 720, 11),
    ("PER-020", "Lizol Disinfectant Surface Cleaner Citrus 500ml", "Personal & Home Care", "Bottle", 88.0, 109.0, 25, 2, 720, 9),
    ("PER-021", "Good Knight Gold Flash Machine + Refill", "Personal & Home Care", "Pack", 78.0, 99.0, 20, 3, 720, 5),
    ("PER-022", "Good Knight Gold Flash Liquid Refill 45ml", "Personal & Home Care", "Bottle", 62.0, 78.0, 30, 2, 720, 10),
    ("PER-023", "All Out Ultra Power+ Refill 45ml", "Personal & Home Care", "Bottle", 60.0, 75.0, 25, 2, 720, 8),
    ("PER-024", "Godrej aer Pocket Bathroom Fragrance 10g", "Personal & Home Care", "Pack", 44.0, 55.0, 20, 3, 720, 6),
    ("PER-025", "Stayfree Secure Cottony Regular Napkins (18s)", "Personal & Home Care", "Pack", 78.0, 95.0, 25, 2, 720, 8),

    # 5. Dairy & Fresh Essentials (15 SKUs) - Margins: 8% - 15%
    ("DAR-001", "Amul Taaza Homogenised Toned Milk 500ml", "Dairy & Fresh Essentials", "Pouch", 25.5, 28.0, 50, 1, 2, 45),
    ("DAR-002", "Amul Gold Full Cream Fresh Milk 500ml", "Dairy & Fresh Essentials", "Pouch", 31.0, 34.0, 50, 1, 2, 38),
    ("DAR-003", "Mother Dairy Toned Milk 500ml", "Dairy & Fresh Essentials", "Pouch", 25.5, 28.0, 30, 1, 2, 22),
    ("DAR-004", "Amul Masti Dahi Pouch 400g", "Dairy & Fresh Essentials", "Pouch", 30.0, 34.0, 25, 1, 5, 18),
    ("DAR-005", "Mother Dairy Classic Curd 400g Tub", "Dairy & Fresh Essentials", "Tub", 38.0, 44.0, 20, 1, 6, 12),
    ("DAR-006", "Amul Pasteurised Butter 100g", "Dairy & Fresh Essentials", "Pack", 50.0, 56.0, 30, 1, 90, 16),
    ("DAR-007", "Amul Pasteurised Butter 500g", "Dairy & Fresh Essentials", "Pack", 245.0, 275.0, 15, 2, 90, 6),
    ("DAR-008", "Amul Malai Fresh Paneer 200g", "Dairy & Fresh Essentials", "Pack", 82.0, 92.0, 20, 1, 15, 14),
    ("DAR-009", "Mother Dairy Fresh Paneer 200g", "Dairy & Fresh Essentials", "Pack", 80.0, 90.0, 15, 1, 15, 10),
    ("DAR-010", "Amul Processed Cheese Slices 200g (10 Slices)", "Dairy & Fresh Essentials", "Pack", 125.0, 145.0, 15, 2, 180, 5),
    ("DAR-011", "Harvest Gold White Bread 400g", "Dairy & Fresh Essentials", "Loaf", 25.0, 30.0, 30, 1, 4, 25),
    ("DAR-012", "Britannia 100% Whole Wheat Bread 400g", "Dairy & Fresh Essentials", "Loaf", 42.0, 50.0, 20, 1, 4, 12),
    ("DAR-013", "Farm Fresh White Eggs (Pack of 6)", "Dairy & Fresh Essentials", "Tray", 42.0, 48.0, 30, 1, 14, 20),
    ("DAR-014", "Farm Fresh White Eggs (Pack of 12)", "Dairy & Fresh Essentials", "Tray", 80.0, 92.0, 25, 1, 14, 15),
    ("DAR-015", "Amul Kool Flavoured Milk Elaichi 180ml", "Dairy & Fresh Essentials", "Can", 22.0, 25.0, 25, 2, 180, 8),
]

SUPPLIERS = [
    {"supplier_id": "SUP-01", "name": "MahaLaxmi FMCG Distributors", "categories": ["Packaged Foods & Snacks", "Personal & Home Care"]},
    {"supplier_id": "SUP-02", "name": "Shree Ganesh Grain & Staples Mandi", "categories": ["Staples & Grains"]},
    {"supplier_id": "SUP-03", "name": "Balaji Oil Trading Agency", "categories": ["Edible Oils & Ghee"]},
    {"supplier_id": "SUP-04", "name": "Amul & Mother Dairy City Depot", "categories": ["Dairy & Fresh Essentials"]},
]


def generate_retail_dataset(
    start_date: date = date(2025, 1, 1),
    days: int = 365,
    seed: int = 42,
    output_dir: str = "dukaanos/data/raw",
) -> Dict[str, pd.DataFrame]:
    """Generates complete, realistic raw datasets for DukaanOS.

    Returns dict of DataFrames:
    - products
    - suppliers
    - inventory_ledger
    - sales_transactions
    - purchase_orders
    """
    random.seed(seed)
    np.random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Products DataFrame
    products_rows = []
    category_supplier_map = {
        "Staples & Grains": "Shree Ganesh Grain & Staples Mandi",
        "Edible Oils & Ghee": "Balaji Oil Trading Agency",
        "Packaged Foods & Snacks": "MahaLaxmi FMCG Distributors",
        "Personal & Home Care": "MahaLaxmi FMCG Distributors",
        "Dairy & Fresh Essentials": "Amul & Mother Dairy City Depot",
    }

    for sku, name, category, unit, cost, price, min_stock, lead_time, shelf_life, base_velocity in CATALOG_SPECS:
        products_rows.append({
            "product_id": sku,
            "product_name": name,
            "category": category,
            "unit": unit,
            "cost_price": cost,
            "selling_price": price,
            "margin_pct": round(((price - cost) / price) * 100, 2),
            "min_reorder_level": min_stock,
            "lead_time_days": lead_time,
            "shelf_life_days": shelf_life,
            "base_daily_velocity": base_velocity,
            "supplier_name": category_supplier_map[category],
        })

    df_products = pd.DataFrame(products_rows)
    df_suppliers = pd.DataFrame(SUPPLIERS)

    # 2. Simulation Setup
    date_list = [start_date + timedelta(days=i) for i in range(days)]

    # Product state tracking
    inventory_state = {}
    for _, prod in df_products.iterrows():
        # Initial stock: 4 to 7 days of base velocity, but at least min_reorder_level + 5
        init_stock = max(int(prod["base_daily_velocity"] * random.uniform(4.0, 7.0)), prod["min_reorder_level"] + 10)
        inventory_state[prod["product_id"]] = {
            "current_stock": init_stock,
            "pending_orders": [],  # list of (delivery_date, qty, po_id)
            "spec": prod,
        }

    ledger_records = []
    sales_records = []
    purchase_orders = []

    tx_counter = 1
    invoice_counter = 1000
    po_counter = 100

    # Record Opening Stock in Ledger
    for sku, state in inventory_state.items():
        ledger_records.append({
            "transaction_id": f"TX-{tx_counter:07d}",
            "date": start_date.strftime("%Y-%m-%d"),
            "product_id": sku,
            "event_type": "OPENING_STOCK",
            "quantity_change": state["current_stock"],
            "running_balance": state["current_stock"],
            "unit_cost": state["spec"]["cost_price"],
            "reference_id": "INIT-2025",
            "notes": "Initial inventory count at system boot",
        })
        tx_counter += 1

    # Festival calendar for 2025 in India
    # Holi: March 14, Diwali: October 20-24, Eid: March 31, New Year/Independence Day
    festivals = {
        date(2025, 3, 13): 1.5,
        date(2025, 3, 14): 1.8,  # Holi
        date(2025, 3, 30): 1.4,
        date(2025, 3, 31): 1.6,  # Eid
        date(2025, 8, 15): 1.3,  # Independence day
        date(2025, 10, 18): 1.5,
        date(2025, 10, 19): 1.8, # Dhanteras
        date(2025, 10, 20): 2.2, # Diwali
        date(2025, 10, 21): 2.0, # Diwali
        date(2025, 12, 31): 1.4, # New Year eve
    }

    # Simulate Day-by-Day
    for current_day in date_list:
        day_str = current_day.strftime("%Y-%m-%d")
        dow = current_day.weekday()  # 5=Sat, 6=Sun
        day_of_month = current_day.day

        # Calendar factors:
        # 1. Weekend factor (Kirana sales jump on Sat & Sun)
        weekend_mult = 1.35 if dow in (5, 6) else 1.0

        # 2. Salary cycle factor: 1st to 7th of every month has ~25% higher staple & pantry purchasing
        salary_mult = 1.25 if day_of_month <= 7 else 1.0

        # 3. Festival multiplier
        festival_mult = festivals.get(current_day, 1.0)

        # Step A: Receive any incoming purchase orders arriving today
        for sku, state in inventory_state.items():
            arrived_orders = [o for o in state["pending_orders"] if o["delivery_date"] <= current_day]
            state["pending_orders"] = [o for o in state["pending_orders"] if o["delivery_date"] > current_day]

            for order in arrived_orders:
                qty_received = order["quantity"]
                state["current_stock"] += qty_received

                ledger_records.append({
                    "transaction_id": f"TX-{tx_counter:07d}",
                    "date": day_str,
                    "product_id": sku,
                    "event_type": "PURCHASE",
                    "quantity_change": qty_received,
                    "running_balance": state["current_stock"],
                    "unit_cost": state["spec"]["cost_price"],
                    "reference_id": order["po_id"],
                    "notes": f"Stock received from {state['spec']['supplier_name']}",
                })
                tx_counter += 1

                # Update PO status
                for po in purchase_orders:
                    if po["po_id"] == order["po_id"]:
                        po["status"] = "RECEIVED"
                        po["received_date"] = day_str

        # Step B: Daily sales for each product
        daily_items_sold = []
        for sku, state in inventory_state.items():
            spec = state["spec"]
            cat = spec["category"]
            base_v = spec["base_daily_velocity"]

            # Multiplier tailored by category
            cat_mult = 1.0
            if cat == "Staples & Grains":
                cat_mult = salary_mult * (1.2 if festival_mult > 1.2 else 1.0)
            elif cat == "Edible Oils & Ghee":
                cat_mult = festival_mult * (1.15 if dow in (5, 6) else 1.0)
            elif cat == "Packaged Foods & Snacks":
                cat_mult = weekend_mult * (1.3 if festival_mult > 1.0 else 1.0)
            elif cat == "Personal & Home Care":
                cat_mult = salary_mult
            elif cat == "Dairy & Fresh Essentials":
                cat_mult = 1.1 if dow in (5, 6) else 1.0

            expected_demand = base_v * cat_mult * random.uniform(0.75, 1.25)
            simulated_demand = np.random.poisson(lam=max(0.2, expected_demand))

            # Stock check: Can we fulfill?
            actual_sold = min(state["current_stock"], simulated_demand)
            lost_sales = simulated_demand - actual_sold

            if actual_sold > 0:
                state["current_stock"] -= actual_sold

                # Record in inventory ledger
                ledger_records.append({
                    "transaction_id": f"TX-{tx_counter:07d}",
                    "date": day_str,
                    "product_id": sku,
                    "event_type": "SALE",
                    "quantity_change": -actual_sold,
                    "running_balance": state["current_stock"],
                    "unit_cost": spec["cost_price"],
                    "reference_id": f"DAILY-{day_str}",
                    "notes": "Store counter sale",
                })
                tx_counter += 1

                # Queue individual product units into daily sales pool
                rem = actual_sold
                while rem > 0:
                    unit_chunk = min(rem, random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0])
                    daily_items_sold.append((sku, spec, unit_chunk))
                    rem -= unit_chunk

            if lost_sales > 0:
                # Log stockout marker
                sales_records.append({
                    "sales_id": f"SLS-{len(sales_records)+1:08d}",
                    "date": day_str,
                    "invoice_id": f"STOCKOUT-{invoice_counter}",
                    "product_id": sku,
                    "product_name": spec["product_name"],
                    "category": spec["category"],
                    "quantity": 0,
                    "unit_price": spec["selling_price"],
                    "cost_price": spec["cost_price"],
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                    "gross_profit": 0.0,
                    "payment_method": "UNFULFILLED",
                    "lost_sales_unfulfilled": lost_sales,
                })
                invoice_counter += 1

        # Natural cross-selling affinities in Kirana shopping baskets
        affinities = {
            "PCK-018": ["STP-013", "STP-014"],  # Red Label Tea + Sugar
            "PCK-019": ["STP-013", "DAR-001"],  # Tata Tea Gold + Sugar or Milk
            "PCK-001": ["PCK-016", "PCK-017"],  # Maggi + Ketchup
            "DAR-011": ["DAR-006", "DAR-007"],  # White Bread + Amul Butter
            "STP-001": ["OIL-001", "OIL-003"],  # Aashirvaad Atta + Mustard/Sunflower Oil
            "PER-001": ["PER-004", "PER-005"],  # Surf Excel + Rin / Vim
        }

        # Pack daily items into realistic multi-product customer baskets
        random.shuffle(daily_items_sold)
        idx = 0
        while idx < len(daily_items_sold):
            basket_invoice = f"INV-{invoice_counter}"
            invoice_counter += 1
            basket_payment = random.choices(["UPI", "CASH", "KHATA_CREDIT"], weights=[0.50, 0.40, 0.10])[0]

            # 1 to 4 items per customer basket
            basket_size = min(random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0], len(daily_items_sold) - idx)
            basket_items = daily_items_sold[idx : idx + basket_size]
            idx += basket_size

            # Check if we can inject an affinity pairing
            if len(basket_items) == 1:
                item_sku = basket_items[0][0]
                if item_sku in affinities and idx < len(daily_items_sold):
                    target_skus = affinities[item_sku]
                    # Find if target sku exists later in today's pool
                    for lookup_idx in range(idx, min(idx + 50, len(daily_items_sold))):
                        if daily_items_sold[lookup_idx][0] in target_skus:
                            # Swap into current basket!
                            basket_items.append(daily_items_sold.pop(lookup_idx))
                            break

            for sku_code, spec_item, chunk_qty in basket_items:
                sales_records.append({
                    "sales_id": f"SLS-{len(sales_records)+1:08d}",
                    "date": day_str,
                    "invoice_id": basket_invoice,
                    "product_id": sku_code,
                    "product_name": spec_item["product_name"],
                    "category": spec_item["category"],
                    "quantity": chunk_qty,
                    "unit_price": spec_item["selling_price"],
                    "cost_price": spec_item["cost_price"],
                    "total_revenue": round(chunk_qty * spec_item["selling_price"], 2),
                    "total_cost": round(chunk_qty * spec_item["cost_price"], 2),
                    "gross_profit": round(chunk_qty * (spec_item["selling_price"] - spec_item["cost_price"]), 2),
                    "payment_method": basket_payment,
                    "lost_sales_unfulfilled": 0,
                })

        # Step C & D: Damage & Reorder checks for ALL SKUs
        for sku, state in inventory_state.items():
            spec = state["spec"]

            # Step C: Occasional Damage / Expiry (Shrinkage is a reality in retail)
            # Probability ~0.3% per product per day
            if state["current_stock"] > 5 and random.random() < 0.003:
                damage_qty = min(state["current_stock"], random.randint(1, 2))
                state["current_stock"] -= damage_qty
                ledger_records.append({
                    "transaction_id": f"TX-{tx_counter:07d}",
                    "date": day_str,
                    "product_id": sku,
                    "event_type": "DAMAGE_EXPIRED",
                    "quantity_change": -damage_qty,
                    "running_balance": state["current_stock"],
                    "unit_cost": spec["cost_price"],
                    "reference_id": "SHRINKAGE",
                    "notes": "Damaged pack / shelf expiry write-off",
                })
                tx_counter += 1

            # Step D: Reorder Logic
            # Check if current stock + pending orders <= min_reorder_level
            total_effective_stock = state["current_stock"] + sum(o["quantity"] for o in state["pending_orders"])
            if total_effective_stock <= spec["min_reorder_level"]:
                # Reorder batch: 7 to 10 days of base velocity
                reorder_qty = max(int(spec["base_daily_velocity"] * random.uniform(7.0, 10.0)), 10)
                lead_days = spec["lead_time_days"]
                deliv_date = current_day + timedelta(days=lead_days)
                po_id = f"PO-{po_counter:06d}"
                po_counter += 1

                po_entry = {
                    "po_id": po_id,
                    "order_date": day_str,
                    "expected_delivery_date": deliv_date.strftime("%Y-%m-%d"),
                    "received_date": None,
                    "product_id": sku,
                    "product_name": spec["product_name"],
                    "supplier_name": spec["supplier_name"],
                    "quantity_ordered": reorder_qty,
                    "unit_cost": spec["cost_price"],
                    "total_po_amount": round(reorder_qty * spec["cost_price"], 2),
                    "status": "ORDERED",
                }
                purchase_orders.append(po_entry)

                state["pending_orders"].append({
                    "delivery_date": deliv_date,
                    "quantity": reorder_qty,
                    "po_id": po_id,
                })

    df_sales = pd.DataFrame(sales_records)
    df_ledger = pd.DataFrame(ledger_records)
    df_po = pd.DataFrame(purchase_orders)

    # Step E: Inject deliberate real-world imperfections into raw files for ETL testing
    # 1. Duplicate records (~1.5% duplicates in sales)
    dup_sample = df_sales.sample(frac=0.015, random_state=seed)
    df_sales_raw = pd.concat([df_sales, dup_sample], ignore_index=True)

    # 2. Missing values (~1% missing payment_method)
    mask = np.random.rand(len(df_sales_raw)) < 0.01
    df_sales_raw.loc[mask, "payment_method"] = np.nan

    # Save to CSV files
    df_products.to_csv(os.path.join(output_dir, "products.csv"), index=False)
    df_suppliers.to_csv(os.path.join(output_dir, "suppliers.csv"), index=False)
    df_sales_raw.to_csv(os.path.join(output_dir, "sales_raw.csv"), index=False)
    df_ledger.to_csv(os.path.join(output_dir, "inventory_ledger.csv"), index=False)
    df_po.to_csv(os.path.join(output_dir, "purchase_orders.csv"), index=False)

    return {
        "products": df_products,
        "suppliers": df_suppliers,
        "sales_raw": df_sales_raw,
        "inventory_ledger": df_ledger,
        "purchase_orders": df_po,
    }


if __name__ == "__main__":
    datasets = generate_retail_dataset()
    print("Dataset generation complete!")
    for name, df in datasets.items():
        print(f"  {name}: {df.shape[0]} rows, {df.shape[1]} columns")

