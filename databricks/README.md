# Databricks

This directory contains the Databricks implementation of the common ETL process defined in `../docs/etl-specification.md`.

## Initial execution with the 100k scenario

1. In the Databricks workspace, create a Unity Catalog volume for experiment files. Record its catalog, schema, and volume names.
2. In that volume, create a `bronze/100k` folder and upload these local files to it:
   - `datasets/100k/customers.csv`
   - `datasets/100k/products.csv`
   - `datasets/100k/transactions.csv`
3. In the Databricks Git folder, open and run `notebooks/01_bronze_to_silver_sales_transactions.py`.
4. Then open and run `notebooks/02_silver_to_gold_monthly_sales.py`.
5. To create delivery artifacts, open and run `notebooks/03_gold_to_delivery_report.py` after the Gold output is validated.
6. At the top of all notebooks, set `CATALOG`, `SCHEMA`, `VOLUME`, and `SCENARIO` to match your workspace.
7. Attach each notebook to an available compute resource and run all cells.

The first notebook writes the managed Delta table `workspace.default.silver_sales_transaction_details_100k`. The second writes the managed Delta table `workspace.default.gold_monthly_sales_by_state_category_100k`. These tables appear in Catalog Explorer and provide the Silver-to-Gold lineage. Each notebook measures its read-transform-write time and then validates the output separately.

The third notebook creates `monthly_sales_by_state_category.csv` and `monthly_sales_executive_report.pdf` under `reports/100k`. This reporting step uses ReportLab and is not part of the ETL performance benchmark.

Do not use the measured time from this initial test as a final research result. It verifies the pipeline. Formal measurements should follow the protocol in `../docs/etl-specification.md`.
