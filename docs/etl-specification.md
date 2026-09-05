# Common ETL Specification

## 1. Purpose

This document defines the ETL process that must be implemented equivalently in Pentaho Data Integration (PDI) and Databricks. Its purpose is to prevent methodological differences between implementations from affecting the performance comparison.

The comparison evaluates the end-to-end execution time and scalability of each platform over the same synthetic input data. It does not evaluate cloud cost, infrastructure provisioning, orchestration, data governance, or production readiness.

## 2. Scope

The ETL process consumes the `customers.csv`, `products.csv`, and `transactions.csv` files of one dataset scenario and produces a Silver transaction-detail dataset and a Gold monthly-sales dataset.

The process includes:

1. Reading the three CSV source files.
2. Cleaning the customer name field.
3. Joining transactions to customers and products.
4. Creating calculated and derived fields.
5. Writing the Silver transaction-detail output.
6. Aggregating Silver data into the Gold monthly-sales output.
7. Validating that the outputs are logically equivalent in both platforms.

The source datasets are valid and contain no nulls, duplicate transaction identifiers, or invalid foreign keys. Therefore, null handling, duplicate removal, error-routing flows, and data rejection rules are outside the initial scope.

## 3. Input datasets

Each experimental scenario is stored in `datasets/<scenario>/` and has the following files.

### 3.1 `customers.csv`

| Field | Type | Description |
| --- | --- | --- |
| `customer_id` | Integer | Unique customer identifier; primary key. |
| `customer_name` | String | Synthetic customer name followed by a numeric suffix. |
| `state` | String | Brazilian state abbreviation. |
| `customer_segment` | String | Customer segment. |

### 3.2 `products.csv`

| Field | Type | Description |
| --- | --- | --- |
| `product_id` | Integer | Unique product identifier; primary key. |
| `product_category` | String | Product category. |
| `unit_price` | Decimal(10,2) | Positive unit price. |

### 3.3 `transactions.csv`

| Field | Type | Description |
| --- | --- | --- |
| `transaction_id` | Integer | Unique transaction identifier; primary key. |
| `customer_id` | Integer | Foreign key to `customers.customer_id`. |
| `product_id` | Integer | Foreign key to `products.product_id`. |
| `transaction_date` | Date | Date in ISO 8601 format (`YYYY-MM-DD`). |
| `quantity` | Integer | Positive quantity. |

## 4. Transformation rules

The two implementations must apply the following rules in the stated logical order. Their physical execution plan may differ according to each platform.

### 4.1 Clean customer names

Source customer names end with a space and the customer identifier, for example `Renato Queiroz 1`.

Create `customer_name_clean` by removing one trailing sequence composed of whitespace followed by one or more digits. The output of `Renato Queiroz 1` must be `Renato Queiroz`.

Conceptual expression:

```text
customer_name_clean = remove trailing " whitespace + digits " from customer_name
```

The original `customer_name` field is not included in the final output.

### 4.2 Join the datasets

Start from `transactions` as the fact dataset.

1. Inner join `transactions.customer_id` to `customers.customer_id`.
2. Inner join `transactions.product_id` to `products.product_id`.

Inner joins are specified because all generated foreign-key references are valid. The result must preserve exactly one output row for each input transaction.

### 4.3 Calculate transaction amount

Create `total_amount` using decimal arithmetic:

```text
total_amount = quantity * unit_price
```

The value must be rounded to two decimal places using the platform's standard half-up decimal rounding mode, or an explicitly equivalent mode. Binary floating-point arithmetic should not be used for this calculation.

### 4.4 Derive date attributes

From `transaction_date`, create:

| Field | Type | Rule |
| --- | --- | --- |
| `transaction_year` | Integer | Four-digit calendar year. |
| `transaction_month` | Integer | Month number from 1 through 12. |

## 5. Silver output contract

The Silver logical output is an enriched transaction dataset with one row per input transaction and the following ordered fields.

| Order | Field | Type | Origin or rule |
| ---: | --- | --- | --- |
| 1 | `transaction_id` | Integer | `transactions.transaction_id` |
| 2 | `customer_id` | Integer | `transactions.customer_id` |
| 3 | `customer_name` | String | Cleaned customer name |
| 4 | `state` | String | `customers.state` |
| 5 | `customer_segment` | String | `customers.customer_segment` |
| 6 | `product_id` | Integer | `transactions.product_id` |
| 7 | `product_category` | String | `products.product_category` |
| 8 | `unit_price` | Decimal(10,2) | `products.unit_price` |
| 9 | `transaction_date` | Date | `transactions.transaction_date` |
| 10 | `transaction_year` | Integer | Derived from transaction date |
| 11 | `transaction_month` | Integer | Derived from transaction date |
| 12 | `quantity` | Integer | `transactions.quantity` |
| 13 | `total_amount` | Decimal(12,2) | `quantity * unit_price` |

The logical output schemas defined here must be equivalent in both platforms. In Databricks, Silver and Gold are implemented as managed Delta tables so they are registered in Unity Catalog and their table-to-table lineage is available. The Bronze source remains CSV files in a Unity Catalog volume.

In Databricks, use the following volume layout:

```text
/Volumes/<catalog>/<schema>/etl_experiment/
└── bronze/<scenario>/
    ├── customers.csv
    ├── products.csv
    └── transactions.csv

<catalog>.<schema>.silver_sales_transaction_details_<scenario>
<catalog>.<schema>.gold_monthly_sales_by_state_category_<scenario>
```

## 6. Gold output contract

The Gold output summarizes Silver transactions at the grain of calendar year, calendar month, state, and product category.

| Order | Field | Type | Rule |
| ---: | --- | --- | --- |
| 1 | `transaction_year` | Integer | Silver `transaction_year` |
| 2 | `transaction_month` | Integer | Silver `transaction_month` |
| 3 | `state` | String | Silver `state` |
| 4 | `product_category` | String | Silver `product_category` |
| 5 | `transaction_count` | Integer | Count of transactions in the group |
| 6 | `total_quantity` | Integer | Sum of `quantity` in the group |
| 7 | `total_sales_amount` | Decimal(16,2) | Sum of `total_amount` in the group |
| 8 | `average_transaction_amount` | Decimal(12,2) | Average of `total_amount` in the group |

## 7. Output validation

Before comparing performance results, validate each run against these conditions:

1. Silver output row count equals the source transaction count for the scenario.
2. `transaction_id` is unique and ranges from 1 to the scenario transaction count.
3. No customer name ends with a numeric suffix.
4. The output contains the 13 specified fields, in the specified order.
5. `quantity`, `unit_price`, and `total_amount` are positive.
6. `transaction_year` and `transaction_month` match `transaction_date`.
7. For a reproducible sample of transaction identifiers, all output fields match between Pentaho and Databricks.
8. The total sum of `total_amount`, grouped row counts by `transaction_year` and `transaction_month`, and the total output row count match between the two platforms.
9. Gold `transaction_count` sums to the Silver output row count, and Gold `total_sales_amount` sums to the Silver `total_amount` sum.

Checks 7 and 8 provide equivalence evidence without requiring a costly full row-by-row comparison of every large output file.

## 8. Performance experiment protocol

### 7.1 Scenarios

Run the same ETL process independently for `100k`, `500k`, `1m`, and `5m`. Do not modify an input dataset after it is generated.

### 7.2 Measured metric

Record elapsed execution time separately for Bronze-to-Silver and Silver-to-Gold. The end-to-end elapsed time is their sum: from the start of source-file reading until the Gold output has been successfully written.

Record the measured time with the same precision for both platforms. Record any execution failure separately; do not replace it with an estimated duration.

### 7.3 Repetitions

For each platform and scenario, execute at least three successful runs. Report individual durations, arithmetic mean, median, minimum, maximum, and standard deviation.

The first run should be identified separately as a warm-up run, because startup, file-system cache, or environment initialization can affect it. The final article should state whether the warm-up run is included in the reported summary; the recommended approach is to exclude it from the main summary and retain it in the raw-results appendix.

### 7.4 Controlled conditions

For a fair comparison, document and keep as stable as possible:

- Hardware or Databricks cluster configuration.
- Operating system and software versions.
- Available memory and processor resources.
- Storage location of source and output files.
- Number of workers or threads, if configured.
- Other workload running on the machine or cluster.
- Pentaho and Databricks configuration relevant to file reading and writing.

The platforms do not need identical internal architectures. The methodology must transparently report differences that cannot be controlled, particularly local execution versus managed cloud execution.

## 9. Results recording

Each completed run should produce one record with, at minimum:

| Field | Description |
| --- | --- |
| `run_id` | Unique run identifier. |
| `platform` | `pentaho` or `databricks`. |
| `scenario` | `100k`, `500k`, `1m`, or `5m`. |
| `pipeline_layer` | `bronze_to_silver`, `silver_to_gold`, or `end_to_end`. |
| `run_number` | Repetition number. |
| `is_warmup` | Whether the run is designated as warm-up. |
| `started_at` | Timestamp with time zone. |
| `elapsed_seconds` | End-to-end elapsed duration. |
| `status` | `success` or `failure`. |
| `output_row_count` | Number of output rows when successful. |
| `total_amount_sum` | Sum of `total_amount` when successful. |
| `notes` | Relevant event, configuration, or error message. |

## 10. Implementation constraints

- Both platforms must use the same source files for a given scenario.
- Both platforms must implement all rules in Sections 4 and 5.
- No platform-specific enrichment, pre-aggregation, filtering, or caching may alter the logical output.
- Any implementation-specific optimization must be documented and must not change the output contract.
- Databricks uses managed Delta tables for Silver and Gold. If Pentaho uses another physical output format, this difference must be documented as a platform-specific storage characteristic when interpreting write-time results.
- The source data and generated outputs must not be committed to Git; code, configurations, documentation, and selected small result summaries may be committed.

## 11. Decisions still required before execution

The following items must be decided and documented before the performance runs begin:

1. Exact Pentaho version and execution mode.
2. Exact Databricks runtime, cluster type, worker count, and storage location.
3. Whether both platforms can access an equivalent storage medium.
4. The final output serialization settings, including CSV delimiter, encoding, header handling, and decimal representation.
5. The tool or script used to calculate and retain the result-validation summaries.
