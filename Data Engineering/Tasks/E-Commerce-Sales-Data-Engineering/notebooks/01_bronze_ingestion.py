"""
E-Commerce Sales Data Engineering - BRONZE LAYER INGESTION
==========================================================
REFERENCE IMPLEMENTATION of the Bronze ingestion step in the
E-Commerce-Sales-Data-Engineering project (Databricks / PySpark / Unity Catalog).

Source: raw e-commerce order records (synthetic/sample dataset) ingested into the
Unity Catalog table workspace.ecommerce.bronze_orders (3,000 raw order rows,
2025-11-26 .. 2026-11-25). The Bronze layer intentionally keeps the raw payload
as-is (including the unit_price column) so Silver can audit and clean it.

Run on a Databricks cluster (or Serverless) with Unity Catalog attached.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

CATALOG = "workspace"
SCHEMA = "ecommerce"

spark = SparkSession.builder.getOrCreate()

RAW_SOURCE = f"{CATALOG}.{SCHEMA}.raw_ecommerce_orders_csv"   # external raw CSV/table staging point
BRONZE = f"{CATALOG}.{SCHEMA}.bronze_orders"

# Column contract of the raw feed (matches bronze_orders exactly):
#   order_id (string), order_date (date), product_name (string), category (string),
#   unit_price (int), city (string), payment_mode (string), order_status (string),
#   quantity (int), amount (int)

raw_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .table(RAW_SOURCE)
)

bronze_df = (
    raw_df
    .withColumn("order_id", F.trim(F.col("order_id")).cast("string"))
    .withColumn("order_date", F.to_date("order_date"))
    .withColumn("unit_price", F.col("unit_price").cast("int"))
    .withColumn("quantity", F.col("quantity").cast("int"))
    .withColumn("amount", F.col("amount").cast("int"))
    .select(
        "order_id", "order_date", "product_name", "category", "unit_price",
        "city", "payment_mode", "order_status", "quantity", "amount",
    )
)

(
    bronze_df.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(BRONZE)
)

row_count = spark.table(BRONZE).count()
print(f"Bronze ingestion complete: {BRONZE} = {row_count:,} rows")
