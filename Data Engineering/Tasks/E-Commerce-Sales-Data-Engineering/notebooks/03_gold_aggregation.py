"""
E-Commerce Sales Data Engineering - GOLD LAYER AGGREGATION
==========================================================
REFERENCE IMPLEMENTATION of the Gold aggregation step. All five gold tables
aggregate DELIVERED orders only (order_status = 'Delivered'), matching the
verified KPIs: 2,316 delivered orders, revenue 38,752,602 INR,
5,798 units sold, AOV 16,732.56 INR, delivery rate 77.2%.

Outputs (Unity Catalog, workspace.ecommerce):
  gold_delivered_orders   - delivered-only fact (grain: order)
  gold_city_sales         - city | orders | units_sold | revenue
  gold_category_sales     - category | orders | units_sold | revenue
  gold_product_sales      - product_name | category | orders | units_sold | revenue
  gold_payment_analysis   - payment_mode | orders | revenue | avg_transaction_value | contribution_pct

Note: lifecycle metrics (Total / Cancelled / Pending orders, cancellation rate)
are computed on the full silver_orders_clean - all valid statuses
(Delivered, Cancelled, Pending) - and are surfaced on the AI/BI dashboard.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

CATALOG = "workspace"
SCHEMA = "ecommerce"

spark = SparkSession.builder.getOrCreate()

SILVER = f"{CATALOG}.{SCHEMA}.silver_orders_clean"
GOLD = f"{CATALOG}.{SCHEMA}"

delivered = spark.table(SILVER).filter(F.col("order_status") == "Delivered")

# 1) Delivered-only fact table
delivered.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{GOLD}.gold_delivered_orders"
)

def write_agg(df, name):
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD}.{name}")

# 2) City aggregate
write_agg(
    delivered.groupBy("city").agg(
        F.countDistinct("order_id").alias("orders"),
        F.sum("quantity").alias("units_sold"),
        F.sum("amount").alias("revenue"),
    ).orderBy(F.desc("revenue")),
    "gold_city_sales",
)

# 3) Category aggregate
write_agg(
    delivered.groupBy("category").agg(
        F.countDistinct("order_id").alias("orders"),
        F.sum("quantity").alias("units_sold"),
        F.sum("amount").alias("revenue"),
    ).orderBy(F.desc("revenue")),
    "gold_category_sales",
)

# 4) Product aggregate (pre-ranked by revenue for the dashboard ranking table)
write_agg(
    delivered.groupBy("product_name", "category").agg(
        F.countDistinct("order_id").alias("orders"),
        F.sum("quantity").alias("units_sold"),
        F.sum("amount").alias("revenue"),
    ).orderBy(F.desc("revenue")),
    "gold_product_sales",
)

# 5) Payment analysis (delivered revenue contribution + avg ticket)
pay = (
    delivered.groupBy("payment_mode").agg(
        F.countDistinct("order_id").alias("orders"),
        F.sum("amount").alias("revenue"),
    )
)
pay = (
    pay.withColumn("avg_transaction_value", F.round(F.col("revenue") / F.col("orders"), 2))
    .withColumn(
        "contribution_pct",
        F.round(F.col("revenue") * 100.0 / F.sum("revenue").over(), 2).cast("decimal(27,2)"),
    )
    .orderBy(F.desc("revenue"))
)
write_agg(pay, "gold_payment_analysis")

total_revenue = delivered.agg(F.sum("amount")).collect()[0][0]
print(f"Gold complete: delivered revenue = {total_revenue:,} INR across 5 gold tables")
