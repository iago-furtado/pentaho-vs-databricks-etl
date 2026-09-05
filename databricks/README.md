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
5. At the top of both notebooks, set `CATALOG`, `SCHEMA`, `VOLUME`, and `SCENARIO` to match your workspace.
6. Attach each notebook to an available compute resource and run all cells.

The first notebook writes CSV output under `silver/100k/sales_transaction_details`. The second writes output under `gold/100k/monthly_sales_by_state_category`. Each measures its read-transform-write time and then validates the output separately.

Do not use the measured time from this initial test as a final research result. It verifies the pipeline. Formal measurements should follow the protocol in `../docs/etl-specification.md`.
