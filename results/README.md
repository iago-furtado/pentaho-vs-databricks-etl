# Results

`experiment_runs.csv` is the versioned log of official controlled experiment runs. It records only small measurement summaries; generated datasets and detailed output files remain outside Git.

`development_runs.csv` preserves exploratory runs that are not eligible for the final performance analysis, such as tests made before the Delta-table architecture was adopted.

The first successful run of each platform and scenario should be marked as `is_warmup=true`. Keep it for traceability, but exclude it from the primary performance summary unless the methodology explicitly states otherwise.
