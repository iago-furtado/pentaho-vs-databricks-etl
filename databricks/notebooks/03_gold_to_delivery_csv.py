# Databricks notebook source
# MAGIC %md
# MAGIC # Gold to delivery CSV
# MAGIC
# MAGIC This notebook creates a delivery-ready CSV from the Gold monthly-sales dataset.
# MAGIC It is post-processing and must not be included in ETL benchmark durations.

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType, LongType

# Replace these values with the catalog, schema, and volume created in your workspace.
CATALOG = "workspace"
SCHEMA = "default"
VOLUME = "etl_experiment"
SCENARIO = "100k"

GOLD_TABLE = f"{CATALOG}.{SCHEMA}.gold_monthly_sales_by_state_category_{SCENARIO}"
REPORT_DIRECTORY = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/reports/{SCENARIO}"
CSV_STAGE_DIRECTORY = f"{REPORT_DIRECTORY}/_monthly_sales_csv_stage"
CSV_REPORT_PATH = f"{REPORT_DIRECTORY}/monthly_sales_by_state_category.csv"

# COMMAND ----------

gold_sales = (
    spark.table(GOLD_TABLE)
    .select(
        F.col("transaction_year").cast(IntegerType()),
        F.col("transaction_month").cast(IntegerType()),
        F.col("state"),
        F.col("product_category"),
        F.col("transaction_count").cast(LongType()),
        F.col("total_quantity").cast(LongType()),
        F.col("total_sales_amount").cast(DecimalType(16, 2)),
        F.col("average_transaction_amount").cast(DecimalType(12, 2)),
    )
)

# COMMAND ----------

# Create one named CSV file for a business recipient. The Gold dataset is small,
# so coalesce(1) is appropriate for this delivery-only step.
dbutils.fs.rm(CSV_STAGE_DIRECTORY, recurse=True)
dbutils.fs.rm(CSV_REPORT_PATH, recurse=True)
(
    gold_sales.coalesce(1).write.mode("overwrite")
    .option("header", "true")
    .option("encoding", "UTF-8")
    .csv(CSV_STAGE_DIRECTORY)
)

part_file = next(
    file_info.path
    for file_info in dbutils.fs.ls(CSV_STAGE_DIRECTORY)
    if file_info.name.startswith("part-") and file_info.name.endswith(".csv")
)
dbutils.fs.mv(part_file, CSV_REPORT_PATH)
dbutils.fs.rm(CSV_STAGE_DIRECTORY, recurse=True)
print(f"CSV delivery file created at: {CSV_REPORT_PATH}")
