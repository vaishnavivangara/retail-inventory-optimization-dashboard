-- =========================================================
-- Retail Inventory Optimization: SQL Layer
-- =========================================================
-- Goal: for each SKU (product_id + store_id), compute:
--   1. average daily demand (units_sold)
--   2. demand volatility (std dev of daily units_sold)
--   3. current inventory level (most recent day on record)
--   4. price, category, region (for business context / $ value)
-- =========================================================

-- 1. Average daily demand + volatility per SKU
--    (SQLite has no native STDEV, so we compute it manually)
DROP VIEW IF EXISTS demand_stats;
CREATE VIEW demand_stats AS
WITH daily AS (
    SELECT
        store_id,
        product_id,
        date,
        units_sold
    FROM sales_inventory
),
agg AS (
    SELECT
        store_id,
        product_id,
        AVG(units_sold) AS avg_daily_demand,
        COUNT(*) AS num_days
    FROM daily
    GROUP BY store_id, product_id
),
variance_calc AS (
    SELECT
        d.store_id,
        d.product_id,
        AVG((d.units_sold - a.avg_daily_demand) * (d.units_sold - a.avg_daily_demand)) AS variance
    FROM daily d
    JOIN agg a
      ON d.store_id = a.store_id AND d.product_id = a.product_id
    GROUP BY d.store_id, d.product_id
)
SELECT
    a.store_id,
    a.product_id,
    a.avg_daily_demand,
    SQRT(v.variance) AS demand_std_dev,
    a.num_days
FROM agg a
JOIN variance_calc v
  ON a.store_id = v.store_id AND a.product_id = v.product_id;


-- 2. Most recent inventory level per SKU (current stock position)
DROP VIEW IF EXISTS current_inventory;
CREATE VIEW current_inventory AS
SELECT
    s.store_id,
    s.product_id,
    s.inventory_level AS current_stock,
    s.date AS as_of_date
FROM sales_inventory s
JOIN (
    SELECT store_id, product_id, MAX(date) AS max_date
    FROM sales_inventory
    GROUP BY store_id, product_id
) latest
  ON s.store_id = latest.store_id
 AND s.product_id = latest.product_id
 AND s.date = latest.max_date;


-- 3. Combined SKU-level summary: demand stats + current stock + price/category
--    This is the table the Python model will read and score.
DROP VIEW IF EXISTS sku_summary;
CREATE VIEW sku_summary AS
SELECT
    ci.store_id,
    ci.product_id,
    p.category,
    p.region,
    p.price,
    ds.avg_daily_demand,
    ds.demand_std_dev,
    ci.current_stock,
    ci.as_of_date
FROM current_inventory ci
JOIN demand_stats ds
  ON ci.store_id = ds.store_id AND ci.product_id = ds.product_id
JOIN (
    SELECT DISTINCT store_id, product_id, category, region, price
    FROM sales_inventory
) p
  ON ci.store_id = p.store_id AND ci.product_id = p.product_id;

-- Sanity check
SELECT * FROM sku_summary LIMIT 10;
