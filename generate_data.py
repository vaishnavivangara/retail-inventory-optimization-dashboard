"""
Generates a synthetic retail sales & inventory dataset that mirrors the
structure of common Kaggle retail inventory datasets:

Columns:
    date, store_id, product_id, category, region,
    inventory_level, units_sold, units_ordered, price, discount

Design choices (so the data actually behaves like real retail data):
- Each product has a base daily demand + its own volatility (some products
  sell steadily, others are erratic).
- Weekly seasonality (weekends sell more).
- Inventory decreases with sales and increases when restocked.
- A handful of products are deliberately made "chronic overstock" and
  "chronic stockout risk" so your dashboard has real patterns to surface.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ---- Config ----
NUM_STORES = 5
NUM_PRODUCTS = 40
NUM_DAYS = 180
START_DATE = datetime(2025, 1, 1)

categories = ["Grocery", "Electronics", "Apparel", "Home & Kitchen", "Personal Care"]
regions = ["North", "South", "East", "West", "Central"]

stores = [f"S{str(i).zfill(3)}" for i in range(1, NUM_STORES + 1)]
store_region = {s: np.random.choice(regions) for s in stores}

products = [f"P{str(i).zfill(4)}" for i in range(1, NUM_PRODUCTS + 1)]
product_category = {p: np.random.choice(categories) for p in products}
product_price = {p: round(np.random.uniform(5, 200), 2) for p in products}

# base demand + volatility per product (this is what creates realistic variation)
product_base_demand = {p: np.random.uniform(2, 25) for p in products}
product_volatility = {p: np.random.uniform(0.15, 0.6) for p in products}  # relative std dev

# deliberately tag some products as overstock-prone (low demand, keep getting restocked)
# and some as stockout-prone (high/spiky demand, restocked too slowly)
overstock_products = set(np.random.choice(products, 6, replace=False))
remaining = [p for p in products if p not in overstock_products]
stockout_products = set(np.random.choice(remaining, 6, replace=False))

rows = []

for store in stores:
    for product in products:
        base_demand = product_base_demand[product]
        vol = product_volatility[product]

        if product in overstock_products:
            base_demand *= 0.4       # sells slowly
            restock_qty = base_demand * 25  # but gets over-ordered
            restock_freq = 14
        elif product in stockout_products:
            base_demand *= 1.8       # sells fast / spiky
            restock_qty = base_demand * 5   # under-ordered relative to demand
            restock_freq = 21
        else:
            restock_qty = base_demand * 12
            restock_freq = 10

        inventory = restock_qty  # starting stock

        for day in range(NUM_DAYS):
            date = START_DATE + timedelta(days=day)
            weekday = date.weekday()
            weekend_boost = 1.3 if weekday >= 5 else 1.0

            demand = max(0, np.random.normal(base_demand * weekend_boost, base_demand * vol))
            demand = round(demand)

            units_sold = min(inventory, demand)
            inventory -= units_sold

            units_ordered = 0
            if day % restock_freq == 0:
                units_ordered = round(restock_qty)
                inventory += units_ordered

            discount = np.random.choice([0, 0, 0, 5, 10, 15], p=[0.6, 0.1, 0.1, 0.1, 0.05, 0.05])

            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "store_id": store,
                "product_id": product,
                "category": product_category[product],
                "region": store_region[store],
                "inventory_level": int(inventory),
                "units_sold": int(units_sold),
                "units_ordered": int(units_ordered),
                "price": product_price[product],
                "discount": discount,
            })

df = pd.DataFrame(rows)
df.to_csv("/home/claude/inventory_project/retail_data.csv", index=False)
print(f"Generated {len(df)} rows")
print(df.head(10).to_string())
