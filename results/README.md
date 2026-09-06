# Results

`experiment_runs.csv` is the versioned log of official controlled experiment runs. It records only small measurement summaries; generated datasets and detailed output files remain outside Git.

`development_runs.csv` preserves exploratory runs that are not eligible for the final performance analysis, such as tests made before the Delta-table architecture was adopted.

Warm-up executions are excluded from primary statistics. Databricks warm-up rows are retained in the log. Pentaho warm-ups were run before the measured series, but their timestamps were not retained consistently; the file therefore contains the three measured Pentaho runs only. This limitation is documented in `../docs/comparative-experiment-results.md`.
