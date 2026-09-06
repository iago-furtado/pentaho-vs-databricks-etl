# Comparative ETL Experiment Results: Pentaho and Databricks

## 1. Purpose of this summary

This document consolidates the measured results to serve as technical input for the MBA article. It compares two implementations of the same business logic: reading customers, products, and transactions; cleaning customer names; joining by `customer_id` and `product_id`; calculating the transaction total; and aggregating by year, month, state, and product category.

The results must be presented as observations from the evaluated environments. They do not support a universal claim of superiority between platforms because Pentaho ran locally and Databricks ran on managed Serverless infrastructure.

## 2. Evaluated implementations

| Platform | Bronze to Silver | Silver to Gold | Silver/Gold storage |
| --- | --- | --- | --- |
| Databricks | PySpark notebook: CSV ingestion, cleaning, joins, derived fields, and write | PySpark notebook: monthly aggregation by state and category | Managed Delta tables in Unity Catalog |
| Pentaho Data Integration 9.4 | `01_bronze_to_silver_sales_transactions.ktr` | `02_silver_to_gold_monthly_sales.ktr` | Local CSV files in `pentaho/output/<scenario>/` |

The Databricks notebooks ran on Databricks Free Edition using Serverless compute. Availability of a `2X-Small` SQL Warehouse is a Free Edition limitation, but it does not define a fixed CPU, memory, or worker configuration for Serverless notebooks.

### 2.1 Pentaho local environment

The Pentaho transformations ran locally in Spoon, using the following configuration recorded after the tests:

| Component | Specification |
| --- | --- |
| Laptop | Dell G3 3500 |
| Processor | Intel Core i5-10300H @ 2.50 GHz (4 cores / 8 logical processors) |
| RAM | 8 GB |
| Storage | 512 GB ADATA NVMe SSD |
| Operating system | Windows 11 Home 64-bit, build 26200 |
| Pentaho Data Integration | 9.4.0.0-343 |
| Java available in the environment | Java 21.0.6 LTS, 64-bit |

This specification describes the observed local environment; it is not a reference configuration for all Pentaho deployments.

### 2.2 Gold schema difference

Databricks Gold includes `average_transaction_amount` in addition to the shared Gold metrics. The current Pentaho Gold transformation produces the shared aggregation grain and three common metrics only: `transaction_count`, `total_quantity`, and `total_sales_amount`. The comparison therefore validates the common aggregation grain, transaction count, and sales total; it is not a byte-for-byte identical Gold schema comparison.

## 3. Dataset scenarios and data validation

| Scenario | Customers | Products | Transactions | Validated sales total |
| --- | ---: | ---: | ---: | ---: |
| 100k | 10,000 | 2,000 | 100,000 | BRL 292,908,411.46 |
| 500k | 50,000 | 10,000 | 500,000 | BRL 1,493,576,980.67 |
| 1m | 100,000 | 20,000 | 1,000,000 | BRL 2,987,230,578.70 |
| 5m | 500,000 | 100,000 | 5,000,000 | BRL 14,942,606,763.93 |

All datasets were generated deterministically with seed `20260827`. For every scenario and both platforms, the sum of Gold `transaction_count` and the sales total matched the expected values. Gold has fewer physical rows because it aggregates data by year, month, state, and category.

## 4. Measurement method

- A warm-up execution was performed before the three measured executions for each scenario and layer; warm-ups were excluded from the statistics.
- In Databricks, time was measured inside the notebooks, covering read, transformation, and managed Delta-table write. Validation occurred after timing ended.
- In Pentaho, time was obtained from the Spoon `Dispatching started` and `The transformation has finished!!` timestamps. Pentaho times therefore have one-second resolution.
- End-to-end times are the sum of the Bronze-to-Silver and Silver-to-Gold means. Databricks CSV/PDF delivery generation is outside the benchmark.
- Pentaho warm-ups were performed before the series, but their timestamps were not systematically retained in the results file; only measured executions are recorded.

## 5. Main results

Times are in seconds; each mean is calculated from three measured executions.

| Scenario | Databricks Bronze-Silver | Databricks Silver-Gold | Databricks end-to-end | Pentaho Bronze-Silver | Pentaho Silver-Gold | Pentaho end-to-end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100k | 2.731 | 2.062 | 4.793 | 1.667 | 2.000 | 3.667 |
| 500k | 3.791 | 2.042 | 5.833 | 5.667 | 8.000 | 13.667 |
| 1m | 4.577 | 1.972 | 6.549 | 9.000 | 25.333 | 34.333 |
| 5m | 6.566 | 2.129 | 8.695 | 50.000 | 124.333 | 174.333 |

### 5.1 Variability of measured executions

Sample standard deviation, in seconds.

| Scenario | Databricks Bronze-Silver | Databricks Silver-Gold | Pentaho Bronze-Silver | Pentaho Silver-Gold |
| --- | ---: | ---: | ---: | ---: |
| 100k | 0.473 | 0.302 | 0.577 | 0.000 |
| 500k | 0.252 | 0.116 | 2.082 | 1.732 |
| 1m | 0.011 | 0.078 | 0.000 | 4.726 |
| 5m | 0.812 | 0.072 | 5.292 | 13.868 |

## 6. Appropriate interpretation of the results

1. In the observed environments, Databricks showed moderate end-to-end time growth from 100k to 5m transactions, increasing from 4.793 s to 8.695 s. The Silver-to-Gold step remained close to two seconds across all scenarios.
2. In local Pentaho, volume growth particularly affected the Silver-to-Gold step. This step sorts and aggregates local CSV files; its mean increased from 2.000 s at 100k to 124.333 s at 5m.
3. At 100k, differences are small and Spoon's one-second resolution limits fine-grained interpretation. The difference in observed behavior becomes clearer from 500k onward.
4. The comparison must account for Databricks writing managed Delta tables and Pentaho writing local CSV files. This is a platform-specific physical and architectural characteristic rather than a fully controlled variable.
5. The infrastructure is also not equivalent: Databricks Serverless is managed and dynamic, whereas Pentaho uses resources from the local laptop. The appropriate conclusion concerns performance measured under these conditions, not every possible deployment of either tool.

## 7. Suggested source text for the article results section

> Equivalent ETL implementations were evaluated in Databricks and Pentaho Data Integration using four deterministic synthetic data volumes, from 100 thousand to 5 million transactions. In every scenario, both implementations preserved the transaction count and aggregate sales value. In the Databricks Free Edition environment using Serverless compute, the mean end-to-end time ranged from 4.793 s at 100k to 8.695 s at 5m. In the local Pentaho environment, mean times ranged from 3.667 s to 174.333 s. Pentaho growth was concentrated primarily in the Silver-to-Gold aggregation, which sorts and groups local CSV files. The results should be interpreted as observations from the evaluated configurations because the platforms used different infrastructure and physical output formats.

## 8. Source records

- Individual executions: `results/experiment_runs.csv`.
- Detailed Databricks results: `docs/databricks-experiment-results.md`.
- Pentaho transformations: `pentaho/transformations/`.
- Pentaho local outputs: `pentaho/output/<scenario>/` (ignored by Git).
