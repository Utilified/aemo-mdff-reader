# nem12-reader

[![CI](https://github.com/utilified/nem12-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/utilified/nem12-reader/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/nem12-reader.svg)](https://pypi.org/project/nem12-reader/)
[![Python versions](https://img.shields.io/pypi/pyversions/nem12-reader.svg)](https://pypi.org/project/nem12-reader/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Fast, zero-dependency streaming reader for AEMO **NEM12** and **NEM13**
metering files.

- O(1) memory — iterate through millions of intervals.
- Pure stdlib core; pandas / PyMySQL are opt-in extras.
- ~2 M readings/sec on the columnar fast path.
- Includes a `nem12-reader` CLI.

## Install

```bash
pip install nem12-reader

# optional extras
pip install nem12-reader[pandas]   # to_dataframe() / parquet
pip install nem12-reader[mysql]    # SQL persistence
```

## Use

```python
from nem12_reader import parse

for r in parse("metering.csv"):
    print(r.nmi, r.interval_start, r.value, r.uom)
```

Or as a flat CSV / DataFrame:

```python
from nem12_reader import parse, write_csv, to_dataframe

write_csv(parse("metering.csv"), "out.csv")     # no pandas
df = to_dataframe("metering.csv")                # needs [pandas]
```

From the command line:

```bash
nem12-reader metering.csv -o out.csv
nem12-reader metering.csv --validate            # spec check
nem12-reader manual.csv --records accumulations # NEM13
```

## API at a glance

| You want                              | Call                          |
| ------------------------------------- | ----------------------------- |
| 300 interval readings (NEM12)         | `parse(src)`                  |
| 250 accumulations (NEM13)             | `parse_accumulations(src)`    |
| Both, in file order                   | `parse_all(src)`              |
| 400 quality / event flags             | `parse_events(src)`           |
| 500 / 550 B2B transactions            | `parse_b2b(src)`              |
| Just the 100 header                   | `parse_header(src)`           |
| Build a pandas DataFrame              | `to_dataframe(src)`           |
| Write a flat CSV (no pandas)          | `write_csv(rows, out)`        |
| Validate against AEMO MDFF v1.02      | `validate_file(src)`          |
| Compute / verify an NMI checksum      | `nmi_checksum`, `validate_nmi`|

`src` can be a path, a file-like object, an iterable of CSV lines, or
an iterable of pre-split rows. The v1 `NEMReader` facade
(`read_from_file`, `to_dataframe`, `to_csv`) still works.

Each `parse(...)` yields an `IntervalReading` with `nmi`,
`meter_serial_number`, `register_id`, `nmi_suffix`, `uom`,
`interval_length`, `interval_date`, `interval_start`, `interval_end`,
`interval_index`, `value`, `quality_method`, `reason_code`,
`reason_description`, `update_datetime`, `msats_load_datetime`. See
the type stubs (`from nem12_reader import IntervalReading`) for the
exact signatures.

## Notes

- **Spec**: AEMO MDFF v1.02 (NEM12 / NEM13). Records `100`, `200`,
  `250`, `300`, `400`, `500`, `550`, `900` are all surfaced; unknown
  indicators are ignored.
- **Tolerant**: UTF-8 BOM is consumed silently, LF and CRLF both work,
  and empty interval cells are coerced to `0.0` (use `quality_method`
  to distinguish missing from zero).
- **Migration from v1**: `NEMReader` still works. The internal
  `nem12_reader.nemstructure` package is gone — see the API table
  above. `pandas` is now opt-in. See `CHANGELOG.md` for details.

## Performance

420,480 readings (4 NMIs × 365 days × 5-min, 2.8 MiB CSV), Python 3.11:

| Operation                          | Time   |
| ---------------------------------- | -----: |
| `for r in parse(path): ...`        | 0.45 s |
| `parse_to_columns(path)`           | 0.21 s |
| `to_dataframe(path)` (pandas)      | 0.76 s |

~2.7× faster than v1 end-to-end; reproduce with
`python benchmarks/bench_parser.py`.

## Development

```bash
git clone https://github.com/utilified/nem12-reader.git
cd nem12-reader
pip install -e .[dev]
pytest
```

CI runs ruff, mypy --strict, the test matrix on Python 3.8 → 3.12 /
Linux / macOS / Windows, `pip-audit`, `bandit`, and a wheel-install
smoke test. Releases are signed with sigstore and published to PyPI
via Trusted Publishing on tag.

## License

MIT — see [LICENSE](LICENSE).
