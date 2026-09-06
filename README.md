# Pentaho vs. Databricks ETL

Reproducible MBA research project that evaluates Pentaho Data Integration (PDI) and Databricks on equivalent sales-data ETL logic across increasing input volumes.

The project includes a deterministic synthetic-data generator, two ETL implementations, validation evidence, and measured execution logs. It is intended to support an academic article; results must be interpreted as observations from the documented local and Serverless environments, not as universal platform claims.

## Project status

The technical experiment is complete.

- Synthetic datasets were generated and validated for `100k`, `500k`, `1m`, and `5m` transaction scenarios.
- The Databricks implementation writes managed Delta Silver and Gold tables in Unity Catalog.
- The Pentaho implementation writes local CSV Silver and Gold outputs.
- Both implementations were executed and validated against transaction counts and sales totals.
- Three measured executions per layer and scenario are recorded in `results/experiment_runs.csv`.

## Complete article

The final MBA article is available in both formats:

- [Read the final article (PDF)](article/Artigo_Pentaho_vs_Databricks_Final.pdf)
- [Editable article source (DOCX)](article/Artigo_Pentaho_vs_Databricks_Final.docx)

## Common ETL logic

```text
Raw CSV files
  customers + products + transactions
             |
             v
Bronze to Silver
  clean customer name, join dimensions, derive date attributes,
  calculate total_amount
             |
             v
Silver to Gold
  aggregate by year, month, state, and product category
```

The common output metrics are `transaction_count`, `total_quantity`, and `total_sales_amount`. See the full transformation contract in [docs/etl-specification.md](docs/etl-specification.md).

## Dataset scenarios

| Scenario | Customers | Products | Transactions |
| --- | ---: | ---: | ---: |
| 100k | 10,000 | 2,000 | 100,000 |
| 500k | 50,000 | 10,000 | 500,000 |
| 1m | 100,000 | 20,000 | 1,000,000 |
| 5m | 500,000 | 100,000 | 5,000,000 |

The datasets are deterministic. Generator seed: `20260827`.

## Repository layout

```text
data_generation/                         Deterministic CSV generator and validator
datasets/                                Locally generated inputs; ignored by Git
databricks/
  notebooks/
    01_bronze_to_silver_sales_transactions.py
    02_silver_to_gold_monthly_sales.py
    03_gold_to_delivery_artifacts.py     Delivery artifacts; outside the benchmark
  README.md                              Databricks setup and execution guidance
pentaho/
  transformations/
    01_bronze_to_silver_sales_transactions.ktr
    02_silver_to_gold_monthly_sales.ktr
  README.md                              Pentaho setup and execution guidance
results/
  experiment_runs.csv                    Individual measured executions
  README.md                              Measurement-log conventions
docs/
  etl-specification.md                   Common transformation contract
  experiment-design.md                   Experimental design
  databricks-experiment-results.md       Databricks measurements
  comparative-experiment-results.md      Consolidated comparison and validation
article/
  appendices/
    source-data-model.dbml                Source code for the ER diagram
    README.md                              Guidance for final article artifacts
tests/                                   Dataset-generation automated test
README.md                                Project overview and reproduction guide
```

The article refers to relevant artifacts by filename. This layout is the canonical map for locating their source, configuration, and execution evidence.

## Local setup and dataset generation

Python 3.10 or later is recommended. The generator uses only the Python standard library, so `requirements.txt` has no installable dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python data_generation/generate_dataset.py --size 100k
python data_generation/validate_dataset.py --size 100k
python -m unittest tests/test_dataset_generation.py
```

Generate the other scenarios by replacing `100k` with `500k`, `1m`, or `5m`. Existing datasets are protected; use `--overwrite` only when intentionally regenerating a scenario.

```powershell
python data_generation/generate_dataset.py --size 5m
python data_generation/validate_dataset.py --size 5m
```

## Run the Pentaho implementation

Prerequisite: Pentaho Data Integration / Spoon 9.4.

1. Generate and validate the desired dataset scenario.
2. Open `pentaho/transformations/01_bronze_to_silver_sales_transactions.ktr` in Spoon.
3. In **Run Options**, set `SCENARIO` in the **Value** column to `100k`, `500k`, `1m`, or `5m`. Leave it blank to use the default `100k`.
4. Run the Bronze-to-Silver transformation. It writes:

   ```text
   pentaho/output/<scenario>/silver_sales_transaction_details.csv
   ```

5. Open and run `pentaho/transformations/02_silver_to_gold_monthly_sales.ktr` with the same `SCENARIO` value. It writes:

   ```text
   pentaho/output/<scenario>/gold_monthly_sales_by_state_category.csv
   ```

The current `.ktr` files contain the original author's absolute Windows project path. If the repository is cloned elsewhere, update the file paths in the Text File Input and Text File Output steps before execution. Generated outputs are ignored by Git.

Additional guidance is in [pentaho/README.md](pentaho/README.md).

## Run the Databricks implementation

Prerequisite: a Databricks workspace with Unity Catalog and Serverless compute.

1. Create or select a Unity Catalog volume.
2. Upload the scenario CSV files to:

   ```text
   /Volumes/<catalog>/<schema>/<volume>/bronze/<scenario>/
   ```

3. In each notebook, configure `CATALOG`, `SCHEMA`, `VOLUME`, and `SCENARIO`.
4. Run the notebooks in order:

   ```text
   databricks/notebooks/01_bronze_to_silver_sales_transactions.py
   databricks/notebooks/02_silver_to_gold_monthly_sales.py
   databricks/notebooks/03_gold_to_delivery_artifacts.py
   ```

The first two notebooks are the benchmarked ETL stages. They write managed Delta tables named:

```text
<catalog>.<schema>.silver_sales_transaction_details_<scenario>
<catalog>.<schema>.gold_monthly_sales_by_state_category_<scenario>
```

The third notebook creates delivery-only CSV/PDF artifacts and is excluded from ETL benchmark durations.

See [databricks/README.md](databricks/README.md) for more detail.

## Measurement protocol

For each platform, scenario, and ETL layer:

1. Run one warm-up execution.
2. Run three measured executions.
3. Exclude warm-ups from the primary statistics.
4. Validate the transaction count and sales total.

Databricks times were captured inside the notebooks, around the read-transform-write operation. Pentaho times were captured from Spoon execution-log timestamps and have one-second resolution. The platforms also use different physical output formats (Delta tables versus local CSV files), so results are not a fully controlled hardware or storage benchmark.

## Results

Individual runs are stored in [results/experiment_runs.csv](results/experiment_runs.csv). The complete comparison, validation evidence, environments, variability, and reporting guidance are in [docs/comparative-experiment-results.md](docs/comparative-experiment-results.md).

| Scenario | Databricks end-to-end mean (s) | Pentaho end-to-end mean (s) |
| --- | ---: | ---: |
| 100k | 4.793 | 3.667 |
| 500k | 5.833 | 13.667 |
| 1m | 6.549 | 34.333 |
| 5m | 8.695 | 174.333 |

## Important implementation difference

Databricks Gold includes `average_transaction_amount` in addition to the shared Gold metrics. The current Pentaho Gold transformation produces the three shared metrics only: `transaction_count`, `total_quantity`, and `total_sales_amount`. Therefore, the comparison validates the common aggregation grain, transaction count, and sales total; it is not a byte-for-byte identical Gold schema comparison.

## Documentation index

- [Experiment design](docs/experiment-design.md)
- [Common ETL specification](docs/etl-specification.md)
- [Databricks experiment results](docs/databricks-experiment-results.md)
- [Comparative experiment results](docs/comparative-experiment-results.md)
- [Data-generation instructions](data_generation/README.md)
- [Pentaho instructions](pentaho/README.md)
- [Databricks instructions](databricks/README.md)
- [Results-log guidance](results/README.md)

## Notes for contributors

Do not commit generated datasets, generated Pentaho outputs, virtual environments, or credentials. Commit source code, `.ktr` definitions, notebook source, small result summaries, and documentation.
