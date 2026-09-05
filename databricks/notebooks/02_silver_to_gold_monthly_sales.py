# Databricks notebook source
# MAGIC %md
# MAGIC # Silver to Gold: monthly sales
# MAGIC
# MAGIC This notebook creates a business-oriented monthly sales summary from the
# MAGIC Silver transaction-detail dataset for one experiment scenario.

# COMMAND ----------

from time import perf_counter

from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType

# Replace these values with the catalog, schema, and volume created in your workspace.
CATALOG = "workspace"
SCHEMA = "default"
VOLUME = "etl_experiment"
SCENARIO = "100k"

SILVER_DIRECTORY = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/silver/{SCENARIO}/sales_transaction_details"
GOLD_DIRECTORY = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/gold/{SCENARIO}/monthly_sales_by_state_category"

# COMMAND ----------

silver_transactions = (
    spark.read.option("header", "true").option("encoding", "UTF-8").csv(SILVER_DIRECTORY)
    .select(
        F.col("transaction_id").cast(IntegerType()),
        F.col("state"),
        F.col("product_category"),
        F.col("transaction_year").cast(IntegerType()),
        F.col("transaction_month").cast(IntegerType()),
        F.col("quantity").cast(IntegerType()),
        F.col("total_amount").cast(DecimalType(12, 2)),
    )
)

# COMMAND ----------

start_time = perf_counter()

monthly_sales = (
    silver_transactions.groupBy(
        "transaction_year",
        "transaction_month",
        "state",
        "product_category",
    )
    .agg(
        F.count("transaction_id").alias("transaction_count"),
        F.sum("quantity").cast("long").alias("total_quantity"),
        F.sum("total_amount").cast(DecimalType(16, 2)).alias("total_sales_amount"),
        F.avg("total_amount").cast(DecimalType(12, 2)).alias("average_transaction_amount"),
    )
    .select(
        "transaction_year",
        "transaction_month",
        "state",
        "product_category",
        "transaction_count",
        "total_quantity",
        "total_sales_amount",
        "average_transaction_amount",
    )
)

# The write is the action that executes the full Silver-to-Gold pipeline.
(
    monthly_sales.write.mode("overwrite")
    .option("header", "true")
    .option("encoding", "UTF-8")
    .csv(GOLD_DIRECTORY)
)

elapsed_seconds = perf_counter() - start_time
print(f"Silver-to-Gold ETL completed in {elapsed_seconds:.3f} seconds.")
print(f"Gold output directory: {GOLD_DIRECTORY}")

# COMMAND ----------

# Validation is intentionally outside the measured ETL time.
gold_output = spark.read.option("header", "true").csv(GOLD_DIRECTORY)
expected_columns = [
    "transaction_year",
    "transaction_month",
    "state",
    "product_category",
    "transaction_count",
    "total_quantity",
    "total_sales_amount",
    "average_transaction_amount",
]

assert gold_output.columns == expected_columns, "Gold output columns do not match the specification."
assert gold_output.count() > 0, "Gold output is empty."
assert gold_output.filter((F.col("transaction_month").cast("int") < 1) | (F.col("transaction_month").cast("int") > 12)).count() == 0, "Invalid transaction month."
assert gold_output.filter((F.col("transaction_count").cast("long") <= 0) | (F.col("total_quantity").cast("long") <= 0) | (F.col("total_sales_amount").cast("decimal(16,2)") <= 0)).count() == 0, "Positive-value validation failed."

validation_summary = gold_output.select(
    F.sum(F.col("transaction_count").cast("long")).alias("aggregated_transaction_count"),
    F.sum(F.col("total_sales_amount").cast("decimal(16,2)")).alias("total_sales_amount_sum"),
).withColumn("scenario", F.lit(SCENARIO)).withColumn("elapsed_seconds", F.lit(elapsed_seconds))

display(validation_summary)
print("Validation passed.")
