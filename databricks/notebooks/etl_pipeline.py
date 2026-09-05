# Databricks notebook source
# MAGIC %md
# MAGIC # Pentaho vs Databricks ETL experiment
# MAGIC
# MAGIC This notebook implements the common ETL specification in
# MAGIC `docs/etl-specification.md` for one dataset scenario.

# COMMAND ----------

from time import perf_counter

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType

# Replace these values with the catalog, schema, and volume created in your workspace.
CATALOG = "workspace"
SCHEMA = "default"
VOLUME = "etl_experiment"
SCENARIO = "100k"

INPUT_DIRECTORY = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{SCENARIO}"
OUTPUT_DIRECTORY = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/results/{SCENARIO}/databricks"
EXPECTED_TRANSACTION_COUNTS = {"100k": 100_000, "500k": 500_000, "1m": 1_000_000, "5m": 5_000_000}

# COMMAND ----------

def read_csv(file_name: str) -> DataFrame:
    """Read a headered UTF-8 CSV file from the experiment volume."""
    return spark.read.option("header", "true").option("encoding", "UTF-8").csv(
        f"{INPUT_DIRECTORY}/{file_name}"
    )


customers = (
    read_csv("customers.csv")
    .select(
        F.col("customer_id").cast(IntegerType()),
        F.regexp_replace(F.col("customer_name"), r"\s+\d+$", "").alias("customer_name"),
        F.col("state"),
        F.col("customer_segment"),
    )
)

products = (
    read_csv("products.csv")
    .select(
        F.col("product_id").cast(IntegerType()),
        F.col("product_category"),
        F.col("unit_price").cast(DecimalType(10, 2)),
    )
)

transactions = (
    read_csv("transactions.csv")
    .select(
        F.col("transaction_id").cast(IntegerType()),
        F.col("customer_id").cast(IntegerType()),
        F.col("product_id").cast(IntegerType()),
        F.to_date(F.col("transaction_date"), "yyyy-MM-dd").alias("transaction_date"),
        F.col("quantity").cast(IntegerType()),
    )
)

# COMMAND ----------

start_time = perf_counter()

enriched_transactions = (
    transactions.join(customers, on="customer_id", how="inner")
    .join(products, on="product_id", how="inner")
    .withColumn("transaction_year", F.year("transaction_date"))
    .withColumn("transaction_month", F.month("transaction_date"))
    .withColumn(
        "total_amount",
        F.round(F.col("quantity") * F.col("unit_price"), 2).cast(DecimalType(12, 2)),
    )
    .select(
        "transaction_id",
        "customer_id",
        "customer_name",
        "state",
        "customer_segment",
        "product_id",
        "product_category",
        "unit_price",
        "transaction_date",
        "transaction_year",
        "transaction_month",
        "quantity",
        "total_amount",
    )
)

# The write is the action that executes the full read-transform-write pipeline.
(
    enriched_transactions.write.mode("overwrite")
    .option("header", "true")
    .option("encoding", "UTF-8")
    .csv(OUTPUT_DIRECTORY)
)

elapsed_seconds = perf_counter() - start_time
print(f"ETL completed in {elapsed_seconds:.3f} seconds.")
print(f"Output directory: {OUTPUT_DIRECTORY}")

# COMMAND ----------

# Validation is intentionally outside the measured ETL time.
output = spark.read.option("header", "true").csv(OUTPUT_DIRECTORY)
expected_columns = [
    "transaction_id", "customer_id", "customer_name", "state", "customer_segment",
    "product_id", "product_category", "unit_price", "transaction_date",
    "transaction_year", "transaction_month", "quantity", "total_amount",
]

assert output.columns == expected_columns, "Output columns do not match the specification."

row_count = output.count()
unique_transaction_count = output.select("transaction_id").distinct().count()
expected_row_count = EXPECTED_TRANSACTION_COUNTS[SCENARIO]
assert row_count == expected_row_count, f"Expected {expected_row_count} rows, found {row_count}."
assert unique_transaction_count == expected_row_count, "transaction_id is not unique."
assert output.filter(F.col("customer_name").rlike(r"\s+\d+$")).count() == 0, "Customer-name cleaning failed."
assert output.filter((F.col("quantity").cast("int") <= 0) | (F.col("unit_price").cast("decimal(10,2)") <= 0) | (F.col("total_amount").cast("decimal(12,2)") <= 0)).count() == 0, "Positive-value validation failed."

validation_summary = output.select(
    F.count("*").alias("output_row_count"),
    F.sum(F.col("total_amount").cast("decimal(12,2)")).alias("total_amount_sum"),
).withColumn("scenario", F.lit(SCENARIO)).withColumn("elapsed_seconds", F.lit(elapsed_seconds))

display(validation_summary)
print("Validation passed.")
