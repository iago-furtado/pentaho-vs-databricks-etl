# Dataset generation

Run the generator from the repository root:

```powershell
python data_generation/generate_dataset.py --size 100k
```

The `--size` option accepts `100k`, `500k`, `1m`, and `5m`. Use `--output-root PATH` to write datasets outside the default `datasets` directory. Generation streams all table rows to CSV. To replace a previously generated scenario, add `--overwrite`.

Validate a generated scenario with:

```powershell
python data_generation/validate_dataset.py --size 100k
```
