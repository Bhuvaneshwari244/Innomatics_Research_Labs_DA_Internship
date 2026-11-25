# Project Workflow — End to End

## 1. Ingest (Bronze)
Raw e-commerce order records (synthetic/sample feed) are landed into the Unity Catalog table
`workspace.ecommerce.bronze_orders` — 3,000 orders spanning 2025-11-26 → 2026-11-25 with ten
columns including the audit-only `unit_price`. The Bronze layer is immutable and unvalidated.

## 2. Clean (Silver)
`02_silver_cleaning.py` applies four validation rules (duplicate `order_id`, invalid amount,
invalid quantity, missing city) and standardizes text casing. Clean rows go to
`silver_orders_clean`; violations are quarantined in `silver_orders_rejected` with a
`reject_reason`. A reconciliation snapshot is written to `gold_data_quality`
(3,000 = 3,000 + 0, `reconciliation_passed = true`).

## 3. Aggregate (Gold)
`03_gold_aggregation.py` filters to `order_status = 'Delivered'` and builds:
- `gold_delivered_orders` — delivered-only fact (2,316 rows)
- `gold_city_sales` — 8 cities
- `gold_category_sales` — 4–5 categories
- `gold_product_sales` — 26 products, pre-ranked by revenue
- `gold_payment_analysis` — payment modes with avg ticket and contribution %

Lifecycle metrics (Total 3,000 / Cancelled 419 / Pending 265, rates) are computed on the full
Silver table because they must include all valid statuses.

## 4. Serve (AI/BI Dashboard)
Dashboard **"E-Commerce Sales Analytics | Gold Layer"** with six sections:
A. Executive Overview (9 KPI cards) · B. Sales Analysis · C. Product Performance
(Top/Bottom 10 + ranking table) · D. Payment Analysis · E. Order Lifecycle & Status ·
F. Data Pipeline & Quality. Global filters: date, city, category, product, payment mode,
order status — each bound only to datasets that carry the dimension, so aggregate tables are
never filtered by dimensions they lack.

## 5. Quality Gate
The dashboard's Data Pipeline & Quality section surfaces `gold_data_quality` live, so any future
re-run that breaks reconciliation (bronze ≠ clean + rejected) is immediately visible on the
dashboard itself.
