# Databricks Experiment Results

## 1. Scope

This document consolidates the Databricks implementation and measured results for the ETL experiment defined in `etl-specification.md`. It is intended as technical input for the academic article and must be interpreted together with the methodological limitations in Section 8.

The Pentaho implementation and its measurements have not yet been performed. Therefore, this document does not make a comparative performance claim between Pentaho and Databricks.

## 2. Databricks implementation

The experiment was implemented in three Databricks notebooks:

| Notebook | Purpose |
| --- | --- |
| `01_bronze_to_silver_sales_transactions.py` | Reads raw CSV files, cleans customer names, joins customers and products to transactions, derives date fields, calculates `total_amount`, and writes a managed Delta Silver table. |
| `02_silver_to_gold_monthly_sales.py` | Reads the Silver table, aggregates sales by year, month, state, and product category, and writes a managed Delta Gold table. |
| `03_gold_to_delivery_artifacts.py` | Creates a delivery CSV and PDF from the Gold table. This notebook is outside the ETL performance benchmark. |

### 2.1 Storage architecture

The Bronze layer stores raw source CSV files in a Unity Catalog Volume:

```text
/Volumes/workspace/default/etl_experiment/bronze/<scenario>/
```

The Silver and Gold layers are managed Delta tables in Unity Catalog:

```text
workspace.default.silver_sales_transaction_details_<scenario>
workspace.default.gold_monthly_sales_by_state_category_<scenario>
```

This design keeps raw files separate from governed Delta tables and makes the Silver-to-Gold dependency available through the Databricks catalog lineage interface.

### 2.2 Execution environment

The implementation and measurements were executed in Databricks Free Edition using Serverless compute. The Free Edition interface reports one SQL Warehouse limited to the `2X-Small` size. This describes the available SQL Warehouse entitlement; it is not a disclosed fixed hardware specification for the Serverless notebook compute used by the PySpark transformations.

The Serverless environment is provider-managed: the user does not select a fixed instance type, processor count, memory allocation, or worker count. Resource allocation may vary between executions, so the experiment reports observed performance in this managed environment rather than performance tied to a fixed hardware specification.

## 3. Dataset scenarios

| Scenario | Customers | Products | Transactions |
| --- | ---: | ---: | ---: |
| 100k | 10,000 | 2,000 | 100,000 |
| 500k | 50,000 | 10,000 | 500,000 |
| 1m | 100,000 | 20,000 | 1,000,000 |
| 5m | 500,000 | 100,000 | 5,000,000 |

All input datasets were generated deterministically with seed `20260827` and validated before upload.

## 4. Measurement method

For every scenario and each ETL layer:

1. One warm-up execution was run and retained for traceability.
2. Three measured executions were run.
3. The warm-up time was excluded from the calculated statistics.
4. Every execution validated the expected transaction count and the total sales amount.

The measured time begins before construction of the transformation pipeline and ends when the managed Delta table is written. Spark transformations are lazy, so this captures the read-transform-write operation. Output validation occurs after timing and is excluded.

The end-to-end value is the mean of the paired Bronze-to-Silver and Silver-to-Gold execution durations. It excludes CSV/PDF delivery generation.

## 5. Results

Times are in seconds. Standard deviation is the sample standard deviation across the three measured executions.

| Scenario | Bronze-to-Silver mean | Silver-to-Gold mean | End-to-end mean | End-to-end SD |
| --- | ---: | ---: | ---: | ---: |
| 100k | 2.731 | 2.062 | 4.793 | 0.775 |
| 500k | 3.791 | 2.042 | 5.833 | 0.359 |
| 1m | 4.577 | 1.972 | 6.549 | 0.071 |
| 5m | 6.566 | 2.129 | 8.695 | 0.873 |

### 5.1 Detailed layer statistics

| Scenario | Bronze-to-Silver SD | Silver-to-Gold SD |
| --- | ---: | ---: |
| 100k | 0.473 | 0.302 |
| 500k | 0.252 | 0.116 |
| 1m | 0.011 | 0.078 |
| 5m | 0.812 | 0.072 |

### 5.2 Data validation evidence

| Scenario | Transaction count | Total sales amount |
| --- | ---: | ---: |
| 100k | 100,000 | BRL 292,908,411.46 |
| 500k | 500,000 | BRL 1,493,576,980.67 |
| 1m | 1,000,000 | BRL 2,987,230,578.70 |
| 5m | 5,000,000 | BRL 14,942,606,763.93 |

The Gold layer preserved the transaction totals and sales amount for every scenario. Its row count is lower because it is an aggregation by year, month, state, and product category.

## 6. Final delivery artifacts

For the 5m scenario, the delivery notebook produced:

```text
/Volumes/workspace/default/etl_experiment/reports/5m/
├── monthly_sales_by_state_category.csv
└── monthly_sales_executive_report.pdf
```

The Gold source table contained 17,496 aggregated rows, representing all 5,000,000 source transactions and BRL 14,942,606,763.93 in total sales. CSV and PDF generation took 13.161 seconds. This duration is reported only as a delivery-processing observation and is excluded from ETL benchmark results.

## 7. Observed behavior

Under the specific Databricks Serverless conditions used in this experiment, the measured end-to-end mean increased from 4.793 seconds for 100k transactions to 8.695 seconds for 5m transactions. This is an observed result in this environment, not a general scalability guarantee.

The Bronze-to-Silver stage accounts for most of the end-to-end duration because it reads raw files, performs joins and transformations, and writes the Silver Delta table. The Silver-to-Gold aggregation was comparatively stable across scenarios.

## 8. Limitations and reporting guidance

- Databricks Serverless startup, resource allocation, caching, and shared infrastructure can affect execution times. Warm-up runs were excluded, but the environment is not fully dedicated.
- Exact Databricks runtime version, serverless configuration, geographic region, and concurrent workload were not captured during these runs. They should be documented if available.
- The Pentaho pipeline must implement equivalent transformations and validations before any direct comparative conclusion is made.
- Databricks writes managed Delta tables. If Pentaho uses a different physical output format, this must be explicitly reported as a platform-specific storage characteristic when interpreting write-time results.
- Results should be presented as measured observations from the stated environment, avoiding unsupported general claims about all Databricks deployments.

## 9. Source records

The complete warm-up and measured-run log is maintained in `results/experiment_runs.csv`. Exploratory tests from the former CSV-output implementation are stored separately in `results/development_runs.csv` and are excluded from the results above.
