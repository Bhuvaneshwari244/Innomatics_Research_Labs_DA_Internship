# Data Dictionary — E-Commerce Sales Data Engineering

All tables live in Unity Catalog under `workspace.ecommerce` (managed Delta tables).
Schemas below reflect the **live catalog**.

## Bronze Layer

### bronze_orders — raw ingested orders (3,000 rows, 2025-11-26 → 2026-11-25)

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Unique order identifier from the source feed |
| `order_date` | date | Date the order was placed |
| `product_name` | string | Product name (raw casing) |
| `category` | string | Product category (raw casing) |
| `unit_price` | int | Unit price — audit-only column, dropped in Silver |
| `city` | string | Delivery city (raw casing) |
| `payment_mode` | string | Payment method (raw casing) |
| `order_status` | string | Delivered / Cancelled / Pending (raw casing) |
| `quantity` | int | Units ordered |
| `amount` | int | Order value = quantity × unit price (raw) |

## Silver Layer

### silver_orders_clean — deduplicated, standardized orders (3,000 rows)

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Unique order identifier (deduplicated, first occurrence kept) |
| `order_date` | date | Order date |
| `product_name` | string | Init-capped, trimmed product name |
| `category` | string | Init-capped, trimmed category |
| `city` | string | Init-capped, trimmed city |
| `payment_mode` | string | Init-capped, trimmed payment mode |
| `order_status` | string | Init-capped, trimmed status (Delivered / Cancelled / Pending) |
| `quantity` | int | Units ordered (> 0 validated) |
| `amount` | int | Order value (> 0 validated) |

*Note: `unit_price` exists only in Bronze/Rejected as an audit column.*

### silver_orders_rejected — quarantined invalid rows (0 rows in the current run)

Same columns as `bronze_orders` plus:

| Column | Type | Description |
|---|---|---|
| `reject_reason` | string | `duplicate_order_id` / `invalid_amount` / `invalid_quantity` / `missing_city` |

## Gold Layer (delivered orders only)

### gold_delivered_orders — delivered-only fact (2,316 rows)

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Delivered order identifier |
| `order_date` | date | Order date |
| `product_name` | string | Standardized product name |
| `category` | string | Standardized category |
| `city` | string | Standardized city |
| `payment_mode` | string | Standardized payment mode |
| `quantity` | int | Units delivered |
| `amount` | int | Delivered order value (INR) |

### gold_city_sales — city aggregate (8 rows)

| Column | Type | Description |
|---|---|---|
| `city` | string | Delivery city |
| `orders` | bigint | Distinct delivered orders |
| `units_sold` | bigint | Units delivered |
| `revenue` | bigint | Delivered revenue (INR) |

### gold_category_sales — category aggregate (4 rows)

Same structure as `gold_city_sales` keyed by `category` (Beauty, Electronics, Fashion, Home & Kitchen, Sports).

### gold_product_sales — product aggregate, pre-ranked by revenue (26 rows)

| Column | Type | Description |
|---|---|---|
| `product_name` | string | Product |
| `category` | string | Product category |
| `orders` | bigint | Distinct delivered orders |
| `units_sold` | bigint | Units delivered |
| `revenue` | bigint | Delivered revenue (INR); table ordered revenue DESC |

### gold_payment_analysis — payment mode aggregate (5 rows)

| Column | Type | Description |
|---|---|---|
| `payment_mode` | string | Payment method |
| `orders` | bigint | Distinct delivered orders |
| `revenue` | bigint | Delivered revenue (INR) |
| `avg_transaction_value` | double | revenue / orders (INR, 2 dp) |
| `contribution_pct` | decimal(27,2) | Share of total delivered revenue (%) |

## Quality Layer

### gold_data_quality — reconciliation snapshot (1 row)

| Column | Type | Description | Current value |
|---|---|---|---|
| `bronze_rows` | bigint | Rows ingested to Bronze | 3,000 |
| `duplicate_rows` | bigint | Duplicate `order_id` rows found | 0 |
| `invalid_amount_rows` | bigint | Rows with amount ≤ 0 / NULL | 0 |
| `invalid_quantity_rows` | bigint | Rows with quantity ≤ 0 / NULL | 0 |
| `missing_city_rows` | bigint | Rows with missing/unknown city | 0 |
| `clean_rows` | bigint | Rows written to `silver_orders_clean` | 3,000 |
| `rejected_rows` | bigint | Rows written to `silver_orders_rejected` | 0 |
| `reconciliation_passed` | boolean | clean + rejected = bronze | true |
