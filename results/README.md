# Results

`experiment_runs.csv` is the versioned log of controlled experiment runs. It records only small measurement summaries; generated datasets and detailed output files remain outside Git.

The first successful run of each platform and scenario should be marked as `is_warmup=true`. Keep it for traceability, but exclude it from the primary performance summary unless the methodology explicitly states otherwise.
