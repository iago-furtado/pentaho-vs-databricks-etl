# Databricks

This directory contains the Databricks implementation of the common ETL process defined in `../docs/etl-specification.md`.

## Execution

1. In the Databricks workspace, create or select a Unity Catalog volume for experiment files.
2. In that volume, create `bronze/<scenario>` and upload these local files:
   - `datasets/<scenario>/customers.csv`
   - `datasets/<scenario>/products.csv`
   - `datasets/<scenario>/transactions.csv`
3. In the Databricks Git folder, open and run `notebooks/01_bronze_to_silver_sales_transactions.py`.
4. Then open and run `notebooks/02_silver_to_gold_monthly_sales.py`.
5. To create delivery artifacts, open and run `notebooks/03_gold_to_delivery_artifacts.py` after the Gold output is validated.
6. At the top of all notebooks, set `CATALOG`, `SCHEMA`, `VOLUME`, and `SCENARIO` to match your workspace and selected scenario (`100k`, `500k`, `1m`, or `5m`).
7. Attach each notebook to an available compute resource and run all cells.

The first notebook writes the managed Delta table `<catalog>.<schema>.silver_sales_transaction_details_<scenario>`. The second writes `<catalog>.<schema>.gold_monthly_sales_by_state_category_<scenario>`. These tables appear in Catalog Explorer and provide Silver-to-Gold lineage. Each notebook measures its read-transform-write time and then validates the output separately.

The third notebook creates `monthly_sales_by_state_category.csv` and `monthly_sales_executive_report.pdf` under `reports/<scenario>`, then displays a delivery summary with its elapsed time. This delivery step is not part of the ETL performance benchmark.

The completed measurements and methodology are documented in `../docs/databricks-experiment-results.md` and `../docs/comparative-experiment-results.md`.
