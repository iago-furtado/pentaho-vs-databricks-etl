# Pentaho Data Integration

This directory contains the local Pentaho Data Integration (PDI) implementation of the common ETL specification in `../docs/etl-specification.md`.

## Transformations

Create and save the following Spoon transformations in `transformations/`:

| File | Purpose |
| --- | --- |
| `01_bronze_to_silver_sales_transactions.ktr` | Reads raw CSV files, cleans customer names, joins customers and products to transactions, calculates derived fields, and writes the Silver output. |
| `02_silver_to_gold_monthly_sales.ktr` | Reads the Silver output, aggregates sales by year, month, state, and product category, and writes the Gold output. |

## Scenario parameter

Both transformations must define a `SCENARIO` parameter. It selects the input dataset and output directory without requiring changes to the transformation design:

```text
100k
500k
1m
5m
```

For local development, use the repository dataset paths:

```text
datasets/<SCENARIO>/
pentaho/output/<SCENARIO>/
```

Generated Pentaho outputs are excluded from Git. The `.ktr` transformation files, documentation, and selected measurement summaries must be committed.

## Measurement approach

For each scenario and transformation:

1. Run one warm-up execution.
2. Run three measured executions.
3. Record the elapsed time, output transaction count, and total sales amount in `../results/experiment_runs.csv`.

The Silver output must contain the same logical fields as the Databricks Silver table. The Gold output must contain the same aggregation grain and metrics as the Databricks Gold table.
