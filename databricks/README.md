# Databricks

This directory contains the Databricks implementation of the common ETL process defined in `../docs/etl-specification.md`.

## Initial execution with the 100k scenario

1. In the Databricks workspace, create a Unity Catalog volume for experiment files. Record its catalog, schema, and volume names.
2. In that volume, create a `100k` folder and upload these local files to it:
   - `datasets/100k/customers.csv`
   - `datasets/100k/products.csv`
   - `datasets/100k/transactions.csv`
3. Create a Python notebook in Databricks and paste the content of `notebooks/etl_pipeline.py`.
4. At the top of the notebook, set `CATALOG`, `SCHEMA`, `VOLUME`, and `SCENARIO` to match your workspace.
5. Attach the notebook to an available compute resource and run all cells.

The notebook writes CSV output under `results/100k/databricks` inside the same volume. It measures end-to-end read-transform-write time, then validates the output separately.

Do not use the measured time from this initial test as a final research result. It verifies the pipeline. Formal measurements should follow the protocol in `../docs/etl-specification.md`.
