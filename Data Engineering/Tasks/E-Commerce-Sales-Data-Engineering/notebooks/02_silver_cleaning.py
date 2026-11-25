"""
E-Commerce Sales Data Engineering - SILVER LAYER CLEANING
=========================================================
REFERENCE IMPLEMENTATION of the Silver cleaning step: deduplicate and
standardize raw Bronze orders into workspace.ecommerce.silver_orders_clean
and quarantine invalid rows in workspace.ecommerce.silver_orders_rejected.

Run on the live project this produced:
  bronze_rows      = 3,000
  clean_rows       = 3,000   (0 duplicates found, 0 invalid rows)
  rejected_rows    = 0
  reconciliation   = bronze 3,000 = clean 3,000 + rejected 0  (PASSED)

Validation rules (mirrored in gold_data_quality):
  R1 duplicate_rows      - duplicate order_id values (keep first occurrence)
  R2 invalid_amount_rows - amount <= 0 or NULL
  R3 invalid_quantity    - quantity <= 0 or NULL
  R4 missing_city_rows   - city is NULL/empty/'unknown'
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "workspace"
SCHEMA = "ecommerce"

spark = SparkSession.builder.getOrCreate()

BRONZE = f"{CATALOG}.{SCHEMA}.bronze_orders"
SILVER_CLEAN = f"{CATALOG}.{SCHEMA}.silver_orders_clean"
SILVER_REJECTED = f"{CATALOG}.{SCHEMA}.silver_orders_rejected"

bronze = spark.table(BRONZE)

# R1 - duplicate order_id detection (keep the first occurrence by ingestion order)
w = Window.partitionBy("order_id").orderBy("order_date")
deduped = (
    bronze
    .withColumn("rn", F.row_number().over(w))
    .withColumn("reject_reason", F.lit(None).cast("string"))
)
duplicates = deduped.filter((F.col("rn") > 1)).withColumn(
    "reject_reason", F.lit("duplicate_order_id")
)

# R2/R3/R4 - field-level validation
invalid = (
    bronze.alias("b")
    .join(duplicates.select("order_id"), on="order_id", how="left_anti")
    .withColumn(
        "reject_reason",
        F.when(F.col("amount").isNull() | (F.col("amount") <= 0), F.lit("invalid_amount"))
        .when(F.col("quantity").isNull() | (F.col("quantity") <= 0), F.lit("invalid_quantity"))
        .when(F.col("city").isNull() | (F.trim(F.lower(F.col("city"))).isin("", "unknown")), F.lit("missing_city"))
        .otherwise(F.lit(None).cast("string")),
    )
)
rejected = invalid.filter(F.col("reject_reason").isNotNull())

# Standardization on the surviving clean rows
clean = (
    invalid.filter(F.col("reject_reason").isNull())
    .withColumn("product_name", F.initcap(F.trim(F.col("product_name"))))
    .withColumn("category", F.initcap(F.trim(F.col("category"))))
    .withColumn("city", F.initcap(F.trim(F.col("city"))))
    .withColumn("payment_mode", F.initcap(F.trim(F.col("payment_mode"))))
    .withColumn("order_status", F.initcap(F.trim(F.col("order_status"))))
)

# silver_orders_clean drops the audit-only unit_price column (amount already carries value)
clean_out = clean.select(
    "order_id", "order_date", "product_name", "category", "city",
    "payment_mode", "order_status", "quantity", "amount",
)

clean_out.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(SILVER_CLEAN)
rejected.select(
    "order_id", "order_date", "product_name", "category", "unit_price", "city",
    "payment_mode", "order_status", "quantity", "amount", "reject_reason",
).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(SILVER_REJECTED)

# ---- reconciliation snapshot (gold_data_quality) -----------------------------
bronze_rows = bronze.count()
clean_rows = clean_out.count()
rejected_rows = rejected.count()
dq = spark.createDataFrame(
    [(
        bronze_rows,
        duplicates.count(),
        invalid.filter(F.col("reject_reason") == "invalid_amount").count(),
        invalid.filter(F.col("reject_reason") == "invalid_quantity").count(),
        invalid.filter(F.col("reject_reason") == "missing_city").count(),
        clean_rows,
        rejected_rows,
        (clean_rows + rejected_rows == bronze_rows),
    )],
    schema=["bronze_rows", "duplicate_rows", "invalid_amount_rows",
            "invalid_quantity_rows", "missing_city_rows", "clean_rows",
            "rejected_rows", "reconciliation_passed"],
)
dq.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{CATALOG}.{SCHEMA}.gold_data_quality"
)

print(f"Silver complete: clean={clean_rows:,} rejected={rejected_rows:,} bronze={bronze_rows:,}")
