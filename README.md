# Retail Inventory Optimization Dashboard

SQL + Python reorder-point model and Power BI dashboard flagging overstock and stockout risk across 200 SKU-store combinations, framed as a business case on working capital vs. stockout risk.

## Problem

Retailers managing hundreds of SKUs across multiple stores face a constant tradeoff: overstocking ties up capital and risks markdowns, while understocking causes lost sales. Tracking this manually across a large product catalog isn't feasible, this project builds a repeatable, data-driven system to flag both risks automatically.

## Approach

**1. SQL** — Aggregated daily sales/inventory transaction data to calculate, per SKU-store combination: average daily demand, demand volatility (standard deviation), and current stock position.

**2. Python** — Built a reorder-point model using the standard inventory formula:
Reorder Point = (Avg Daily Demand x Lead Time) + Safety Stock
Safety Stock = Z-score x Demand Std Dev x sqrt(Lead Time)

Each SKU is compared against its reorder point and flagged as **Stockout Risk**, **Overstock**, or **Healthy**. Business impact is quantified in dollars: capital tied up in excess stock, and revenue at risk from potential stockouts.

**3. Power BI** — Interactive dashboard with KPI cards, category-level breakdowns, and a filterable SKU-level detail table, allowing a store manager to drill from a high-level dollar figure down to the exact products driving it.

## Key Results

- **$4.13M** in capital tied up across overstocked SKUs
- **$114K** in at-risk revenue from SKUs nearing stockout
- **200** SKU-store combinations analyzed across 5 stores and 5 product categories

## Files

| File | Description |
|---|---|
| `generate_data.py` | Generates the synthetic retail sales/inventory dataset |
| `retail_data.csv` | Raw daily sales and inventory data |
| `analysis_queries.sql` | SQL layer: demand statistics and current stock position per SKU |
| `reorder_model.py` | Python reorder-point model and risk flagging logic |
| `reorder_analysis.csv` | Final SKU-level output (input to Power BI) |
| `retail_inventory_dashboard.pbix` | Power BI dashboard file |

## Tech Stack

SQL (SQLite) - Python (pandas, numpy) - Power BI

## Note on Data

This project uses a synthetic dataset generated to mirror the structure and patterns of real retail sales/inventory data (daily sales, stock levels, pricing across stores and categories), since a clean public dataset with all required fields wasn't available. The methodology applies identically to real transactional data.
