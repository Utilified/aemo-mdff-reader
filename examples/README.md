# Examples

Small, self-contained scripts that show common workflows on top of
`aemo-mdff-reader`. Each one runs against the bundled fixture out of the
box:

```bash
python examples/01_load_and_inspect.py    tests/fixtures/sample_nem12.csv
python examples/02_daily_totals.py        tests/fixtures/sample_nem12.csv > daily.csv
python examples/03_filter_to_dataframe.py tests/fixtures/sample_nem12.csv NMI1234567
python examples/04_validate.py            tests/fixtures/sample_nem12.csv
```

| Script | What it shows |
| ------ | ------------- |
| [`01_load_and_inspect.py`](01_load_and_inspect.py) | Header, channel inventory, quality-flag breakdown, date range — using only `parse()` and `parse_header()`. |
| [`02_daily_totals.py`](02_daily_totals.py)         | Streaming roll-up to daily kWh per channel using `aemo_mdff_reader.aggregate.daily_totals`. |
| [`03_filter_to_dataframe.py`](03_filter_to_dataframe.py) | Filter by NMI / date in pandas (fast path) and via a streaming generator (low memory). Requires the `[pandas]` extra. |
| [`04_validate.py`](04_validate.py)                 | Programmatic spec validation via `validate_file`. |

Need a different recipe? The streaming `parse()` + standard-library
`itertools` / `csv` / `datetime` get most jobs done in a few lines.
