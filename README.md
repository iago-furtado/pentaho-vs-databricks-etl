# Pentaho vs Databricks ETL

This repository supports an academic experiment comparing Pentaho Data Integration (PDI) and Databricks during equivalent ETL processes with increasing data volumes.

## Current scope

The first phase provides a reproducible, synthetic sales dataset. The ETL transformations themselves have not yet been defined or implemented.

## Experimental dataset

Each scenario contains `customers.csv`, `products.csv`, and `transactions.csv`. Transactions are the fact table and determine the scale.

| Scenario | Customers | Products | Transactions |
| --- | ---: | ---: | ---: |
| 100k | 10,000 | 2,000 | 100,000 |
| 500k | 50,000 | 10,000 | 500,000 |
| 1m | 100,000 | 20,000 | 1,000,000 |
| 5m | 500,000 | 100,000 | 5,000,000 |

The generated files are deliberately excluded from Git. Anyone can reproduce them with the generator.

## Setup

This project currently has no third-party Python dependencies. Python 3.10 or later is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python data_generation/generate_dataset.py --size 100k
python data_generation/validate_dataset.py --size 100k
```

Use the same commands with `500k`, `1m`, or `5m` to generate another scenario. Existing datasets are protected; add `--overwrite` only when you intentionally want to regenerate a scenario.

## Reproducibility

The generator uses only the Python standard library and a fixed seed (`20260827`). It writes CSV rows incrementally, so transactions are not held in memory. Re-running a command from the same code version produces equivalent files.

## Repository layout

```text
data_generation/  Dataset generator and streaming validator
datasets/         Locally generated CSV datasets (not committed)
pentaho/          Reserved for the future PDI implementation
databricks/       Reserved for the future Databricks implementation
results/          Reserved for experiment outputs
docs/             Experiment design documentation
tests/            Automated checks
```

Before the ETL implementations begin, the exact transformations and measurement protocol must be defined so both platforms process equivalent inputs and outputs.

The defined common process is documented in [the ETL specification](docs/etl-specification.md).
