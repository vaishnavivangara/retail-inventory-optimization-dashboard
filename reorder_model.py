"""
Reorder Point Model
====================
Reads the sku_summary view (built by SQL) and, for each SKU, calculates:

  Reorder Point (ROP) = (Avg Daily Demand x Lead Time)
                         + Safety Stock

  Safety Stock = Z x Demand Std Dev x sqrt(Lead Time)

Where:
  - Lead Time: days between placing an order and receiving stock.
    Not present in the raw data, so we assign it as a realistic
    assumption per category (this is normal in real inventory
    projects - lead time is a supplier-level input, not something
    you derive from sales history).
  - Z: service level factor. Z=1.65 -> ~95% service level
    (i.e. we accept a 5% chance of stocking out before the next
    delivery arrives). This is a standard industry default.

Then each SKU is flagged:
  - "Stockout Risk"  -> current_stock < reorder_point
  - "Overstock"      -> current_stock > reorder_point x OVERSTOCK_MULTIPLIER
  - "Healthy"         -> in between

Business value is also calculated:
  - capital_tied_up = value of stock sitting beyond what's needed
  - at_risk_revenue = potential lost sales if stockout isn't addressed
"""

import sqlite3
import pandas as pd
import numpy as np

# ---- Assumptions (clearly separated so they're easy to defend/tune) ----
LEAD_TIME_DAYS = {
    "Grocery": 3,
    "Electronics": 14,
    "Apparel": 10,
    "Home & Kitchen": 7,
    "Personal Care": 5,
}
Z_SCORE = 1.65          # ~95% service level
OVERSTOCK_MULTIPLIER = 2.0   # stock > 2x reorder point = overstock

# ---- Load data from SQLite (output of the SQL layer) ----
conn = sqlite3.connect("/home/claude/inventory_project/inventory.db")
df = pd.read_sql("SELECT * FROM sku_summary", conn)
conn.close()

# ---- Apply lead time per category ----
df["lead_time_days"] = df["category"].map(LEAD_TIME_DAYS)

# ---- Reorder point calculation ----
df["safety_stock"] = Z_SCORE * df["demand_std_dev"] * np.sqrt(df["lead_time_days"])
df["reorder_point"] = (df["avg_daily_demand"] * df["lead_time_days"]) + df["safety_stock"]

# ---- Flagging logic ----
def flag_status(row):
    if row["current_stock"] < row["reorder_point"]:
        return "Stockout Risk"
    elif row["current_stock"] > row["reorder_point"] * OVERSTOCK_MULTIPLIER:
        return "Overstock"
    else:
        return "Healthy"

df["status"] = df.apply(flag_status, axis=1)

# ---- Business impact ----
# Capital tied up: value of stock beyond the healthy ceiling (reorder_point x multiplier)
df["excess_units"] = np.where(
    df["status"] == "Overstock",
    df["current_stock"] - (df["reorder_point"] * OVERSTOCK_MULTIPLIER),
    0
)
df["capital_tied_up"] = (df["excess_units"] * df["price"]).round(2)

# At-risk revenue: if stockout risk, estimate days of lost sales until
# next likely restock (using lead time as a proxy) x avg demand x price
df["shortfall_units"] = np.where(
    df["status"] == "Stockout Risk",
    (df["reorder_point"] - df["current_stock"]).clip(lower=0),
    0
)
df["at_risk_revenue"] = (
    np.minimum(df["shortfall_units"], df["avg_daily_demand"] * df["lead_time_days"])
    * df["price"]
).round(2)

# ---- Round for readability ----
df["avg_daily_demand"] = df["avg_daily_demand"].round(2)
df["demand_std_dev"] = df["demand_std_dev"].round(2)
df["safety_stock"] = df["safety_stock"].round(2)
df["reorder_point"] = df["reorder_point"].round(2)

# ---- Save output for Power BI ----
output_cols = [
    "store_id", "product_id", "category", "region", "price",
    "avg_daily_demand", "demand_std_dev", "lead_time_days",
    "safety_stock", "reorder_point", "current_stock", "status",
    "capital_tied_up", "at_risk_revenue", "as_of_date"
]
df[output_cols].to_csv("/home/claude/inventory_project/reorder_analysis.csv", index=False)

# ---- Console summary ----
print("=== Status Breakdown ===")
print(df["status"].value_counts())
print()
print(f"Total capital tied up in overstock: ${df['capital_tied_up'].sum():,.2f}")
print(f"Total at-risk revenue from stockouts: ${df['at_risk_revenue'].sum():,.2f}")
print()
print("Sample rows:")
print(df[output_cols].head(10).to_string())
