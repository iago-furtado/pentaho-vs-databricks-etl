# Databricks notebook source
# MAGIC %md
# MAGIC # Gold to delivery report
# MAGIC
# MAGIC This notebook creates delivery artifacts from the Gold monthly-sales dataset.
# MAGIC It is post-processing and must not be included in ETL benchmark durations.

# COMMAND ----------

# MAGIC %pip install reportlab

# COMMAND ----------

from datetime import datetime, timezone
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType, LongType
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Replace these values with the catalog, schema, and volume created in your workspace.
CATALOG = "workspace"
SCHEMA = "default"
VOLUME = "etl_experiment"
SCENARIO = "100k"

GOLD_TABLE = f"{CATALOG}.{SCHEMA}.gold_monthly_sales_by_state_category_{SCENARIO}"
REPORT_DIRECTORY = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/reports/{SCENARIO}"
CSV_STAGE_DIRECTORY = f"{REPORT_DIRECTORY}/_monthly_sales_csv_stage"
CSV_REPORT_PATH = f"{REPORT_DIRECTORY}/monthly_sales_by_state_category.csv"
PDF_REPORT_PATH = f"{REPORT_DIRECTORY}/monthly_sales_executive_report.pdf"

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

# COMMAND ----------

summary = gold_sales.agg(
    F.sum("transaction_count").alias("transaction_count"),
    F.sum("total_quantity").alias("total_quantity"),
    F.sum("total_sales_amount").alias("total_sales_amount"),
).first()

monthly_totals = (
    gold_sales.groupBy("transaction_year", "transaction_month")
    .agg(F.sum("total_sales_amount").alias("total_sales_amount"))
    .orderBy("transaction_year", "transaction_month")
    .collect()
)
top_states = (
    gold_sales.groupBy("state")
    .agg(F.sum("total_sales_amount").alias("total_sales_amount"))
    .orderBy(F.desc("total_sales_amount"))
    .limit(5)
    .collect()
)
top_categories = (
    gold_sales.groupBy("product_category")
    .agg(F.sum("total_sales_amount").alias("total_sales_amount"))
    .orderBy(F.desc("total_sales_amount"))
    .limit(5)
    .collect()
)


def format_currency(value: object) -> str:
    return f"BRL {float(value):,.2f}"


def build_table(data: list[list[str]], widths: list[float]) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E2F3")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F9FD")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


# Databricks serverless compute blocks access to arbitrary local paths such as
# /tmp. Write the PDF directly to the Unity Catalog volume instead.
dbutils.fs.rm(PDF_REPORT_PATH, recurse=True)
styles = getSampleStyleSheet()
document = SimpleDocTemplate(
    PDF_REPORT_PATH,
    pagesize=A4,
    rightMargin=1.5 * cm,
    leftMargin=1.5 * cm,
    topMargin=1.5 * cm,
    bottomMargin=1.5 * cm,
)
story = [
    Paragraph("Monthly Sales Executive Report", styles["Title"]),
    Paragraph(f"Scenario: {SCENARIO} | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]),
    Spacer(1, 0.4 * cm),
    Paragraph("Executive summary", styles["Heading2"]),
]

kpi_data = [
    ["Metric", "Value"],
    ["Transactions", f"{summary['transaction_count']:,}"],
    ["Items sold", f"{summary['total_quantity']:,}"],
    ["Total sales", format_currency(summary["total_sales_amount"])],
]
story.extend([build_table(kpi_data, [7 * cm, 8 * cm]), Spacer(1, 0.45 * cm)])

monthly_data = [["Year", "Month", "Total sales"]] + [
    [str(row["transaction_year"]), str(row["transaction_month"]), format_currency(row["total_sales_amount"])]
    for row in monthly_totals
]
story.extend([Paragraph("Sales by month", styles["Heading2"]), build_table(monthly_data, [3 * cm, 3 * cm, 9 * cm]), Spacer(1, 0.45 * cm)])

states_data = [["State", "Total sales"]] + [
    [row["state"], format_currency(row["total_sales_amount"])] for row in top_states
]
categories_data = [["Product category", "Total sales"]] + [
    [row["product_category"], format_currency(row["total_sales_amount"])] for row in top_categories
]
story.extend(
    [
        Paragraph("Top five states", styles["Heading2"]),
        build_table(states_data, [7 * cm, 8 * cm]),
        Spacer(1, 0.45 * cm),
        Paragraph("Top five product categories", styles["Heading2"]),
        build_table(categories_data, [7 * cm, 8 * cm]),
    ]
)
document.build(story)
print(f"PDF delivery file created at: {PDF_REPORT_PATH}")
