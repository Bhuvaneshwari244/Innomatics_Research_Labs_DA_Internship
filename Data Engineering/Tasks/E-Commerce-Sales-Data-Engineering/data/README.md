# data/ — Source Data

The project uses a **synthetic/sample e-commerce order dataset** that lives directly in
Unity Catalog under `workspace.ecommerce` (no external files need to be downloaded to run
the pipeline as configured).

## Table Inventory

| Table | Layer | Rows | Content |
|---|---|---|---|
| `bronze_orders` | Bronze | 3,000 | Raw orders, 2025-11-26 → 2026-11-25 |
| `silver_orders_clean` | Silver | 3,000 | Deduplicated, standardized orders |
| `silver_orders_rejected` | Silver | 0 | Quarantined invalid rows |
| `gold_delivered_orders` | Gold | 2,316 | Delivered-only fact |
| `gold_city_sales` | Gold | 8 | City aggregates (delivered) |
| `gold_category_sales` | Gold | 5 | Category aggregates (delivered) |
| `gold_product_sales` | Gold | 26 | Product aggregates (delivered), revenue-ranked |
| `gold_payment_analysis` | Gold | 5 | Payment mode aggregates (delivered) |
| `gold_data_quality` | Quality | 1 | Reconciliation snapshot |

Order statuses: **Delivered (2,316), Cancelled (419), Pending (265)**.
This folder intentionally contains no data files — the pipeline reads from and writes to
Unity Catalog managed Delta tables.
