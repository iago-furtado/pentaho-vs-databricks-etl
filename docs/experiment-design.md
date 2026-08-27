# Experiment Design

## Objective

Evaluate how Pentaho Data Integration and Databricks behave when executing equivalent ETL processes over increasing volumes of synthetic sales data.

## Design principles

- Reproducible and controlled execution.
- Identical input records and equivalent transformation/output logic for both platforms.
- No unnecessary infrastructure or technologies.
- Initial focus on execution time and scalability.

## Source model

`customers` contains customer identifiers, synthetic names, Brazilian state abbreviations, and segments. `products` contains product identifiers, categories, and prices. `transactions` references both dimensions and contains a date and positive quantity.

All foreign keys are valid. The initial data is clean; controlled quality issues are explicitly out of scope until a later decision.

## Scenarios

| Scenario | Customers | Products | Transactions |
| --- | ---: | ---: | ---: |
| 100k | 10,000 | 2,000 | 100,000 |
| 500k | 50,000 | 10,000 | 500,000 |
| 1m | 100,000 | 20,000 | 1,000,000 |
| 5m | 500,000 | 100,000 | 5,000,000 |

## Dataset reproducibility

The generator uses seed `20260827` and independent deterministic random streams for each table. It writes directly to CSV files, avoiding an in-memory transaction table. The validator reads CSV files row by row and verifies headers, row counts, sequential unique identifiers, reference ranges, positive quantities and prices, and the configured date range.

## Future phases

1. Define equivalent ETL transformations and outputs (documented in `etl-specification.md`).
2. Implement the Pentaho pipeline.
3. Implement the Databricks pipeline.
4. Execute controlled runs and record measurements.
5. Analyze and report results.
