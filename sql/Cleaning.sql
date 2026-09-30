-- =====================================================================
-- Olist Cohort Retention Analysis: Data Pipeline (PostgreSQL)
-- =====================================================================
-- Input:  olist_customers_dataset.csv, olist_orders_dataset.csv
--         (Brazilian E-Commerce Public Dataset by Olist, via Kaggle)
-- Output: olist_clean table, exported to data/olist_clean.csv for the
--         Python cohort analysis (cohort_analysis.py)
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. Create the raw staging tables
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS olist_customers;

CREATE TABLE olist_customers (
    customer_id               TEXT,
    customer_unique_id        TEXT,
    customer_zip_code_prefix  TEXT,
    customer_city             TEXT,
    customer_state            TEXT
);

DROP TABLE IF EXISTS olist_orders;

CREATE TABLE olist_orders (
    order_id                        TEXT,
    customer_id                     TEXT,
    order_status                    TEXT,
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP
);


-- ---------------------------------------------------------------------
-- 2. Load the raw CSVs
-- ---------------------------------------------------------------------
-- Run from a psql terminal session, since \copy reads the file from the
-- client machine rather than the server. Adjust paths as needed.
--
-- \copy olist_customers FROM 'path\to\olist_customers_dataset.csv' WITH (FORMAT csv, HEADER true);
-- \copy olist_orders FROM 'path\to\olist_orders_dataset.csv' WITH (FORMAT csv, HEADER true);

SELECT COUNT(*) FROM olist_customers;  -- expect 99,441
SELECT COUNT(*) FROM olist_orders;     -- expect 99,441


-- ---------------------------------------------------------------------
-- 3. Explore data quality before joining
-- ---------------------------------------------------------------------
-- Important: customer_id is unique PER ORDER in this dataset.
-- customer_unique_id identifies the actual person across multiple orders.
-- Grouping by customer_id instead would make every customer look like a
-- one-time buyer and break retention analysis entirely.
SELECT COUNT(*) AS total_customer_ids,
       COUNT(DISTINCT customer_unique_id) AS distinct_people
FROM olist_customers;

-- Order status breakdown (not filtered out -- kept via a flag instead,
-- so non-delivered orders remain available for other questions later)
SELECT order_status, COUNT(*) FROM olist_orders GROUP BY order_status;


-- ---------------------------------------------------------------------
-- 4. Build the joined, cleaned table
-- ---------------------------------------------------------------------
-- Joins orders to customers to attach the real customer_unique_id to
-- each order, and adds an is_delivered flag rather than deleting
-- non-delivered rows.
DROP TABLE IF EXISTS olist_clean;

CREATE TABLE olist_clean AS
SELECT
    o.order_id,
    c.customer_unique_id,
    o.order_status,
    (o.order_status = 'delivered') AS is_delivered,
    o.order_purchase_timestamp,
    c.customer_state
FROM olist_orders o
JOIN olist_customers c
    ON o.customer_id = c.customer_id;

-- Sanity checks
SELECT COUNT(*) FROM olist_clean;                               -- expect 99,441 (join drops/duplicates nothing)
SELECT COUNT(DISTINCT customer_unique_id) FROM olist_clean;     -- expect 96,096
SELECT is_delivered, COUNT(*) FROM olist_clean GROUP BY is_delivered;


-- ---------------------------------------------------------------------
-- 5. Export the cleaned table for the Python cohort analysis
-- ---------------------------------------------------------------------
-- Run from a psql terminal session:
--
-- \copy olist_clean TO 'path\to\data\olist_clean.csv' WITH (FORMAT csv, HEADER true);
