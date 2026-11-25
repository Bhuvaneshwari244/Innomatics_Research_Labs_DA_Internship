# Data Quality & Reconciliation

## Pipeline Reconciliation (gold_data_quality)

| Check | Result |
|---|---|
| Bronze rows ingested | 3,000 |
| Clean rows written to Silver | 3,000 |
| Rejected rows quarantined | 0 |
| Duplicate order IDs | 0 |
| Invalid amount rows | 0 |
| Invalid quantity rows | 0 |
| Missing city rows | 0 |
| `clean_rows + rejected_rows = bronze_rows` | ✅ 3,000 = 3,000 + 0 |
| `reconciliation_passed` | ✅ true |

## Validation Rules

- **R1 Duplicate order IDs** — `row_number()` over `order_id` keeps the first occurrence; extra
  occurrences are quarantined with `reject_reason = 'duplicate_order_id'`.
- **R2 Amount validity** — `amount` must be > 0 and non-null.
- **R3 Quantity validity** — `quantity` must be > 0 and non-null.
- **R4 City presence** — `city` must not be NULL / empty / 'unknown'.
- **Standardization** — names, categories, cities, payment modes and statuses are init-capped and
  trimmed before Silver is written.

## Business Reconciliation (verified on the AI/BI dashboard)

| Check | Result |
|---|---|
| Total Orders = Delivered + Cancelled + Pending | ✅ 2,316 + 419 + 265 = 3,000 |
| Delivery Rate = Delivered / Total | ✅ 2,316 / 3,000 = 77.2% |
| Cancellation Rate = Cancelled / Total | ✅ 419 / 3,000 = 14.0% |
| Total Revenue (delivered only) | ✅ ₹38,752,602 |
| Σ `gold_city_sales.revenue` = Total Revenue | ✅ 8 cities sum to 38,752,602 |
| Σ `gold_product_sales.revenue` = Total Revenue | ✅ 26 products sum to 38,752,602 |
| Σ `gold_payment_analysis.revenue` = Total Revenue | ✅ 5 modes sum to 38,752,602 |
| Units Sold (delivered) | ✅ 5,798 |
| Average Order Value | ✅ 38,752,602 / 2,316 = ₹16,732.56 |
| Product ranking table = Top-10 chart order | ✅ rank 1 Smartphone, rank 2 Laptop |

## Known Limitations

- Status metrics (Total / Cancelled / Pending, delivery & cancellation rates) are computed on
  `silver_orders_clean` (all valid statuses); gold aggregates are delivered-only by design.
- The dataset is synthetic/sample data; there are no PII or compliance constraints.
