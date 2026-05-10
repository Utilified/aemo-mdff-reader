# aemo-mdff-reader

[![CI](https://github.com/Utilified/aemo-mdff-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/Utilified/aemo-mdff-reader/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/aemo-mdff-reader.svg)](https://pypi.org/project/aemo-mdff-reader/)
[![Python versions](https://img.shields.io/pypi/pyversions/aemo-mdff-reader.svg)](https://pypi.org/project/aemo-mdff-reader/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CodeQL](https://github.com/Utilified/aemo-mdff-reader/actions/workflows/codeql.yml/badge.svg)](https://github.com/Utilified/aemo-mdff-reader/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Utilified/aemo-mdff-reader/badge)](https://scorecard.dev/viewer/?uri=github.com/Utilified/aemo-mdff-reader)

Fast, zero-dependency streaming reader for AEMO **NEM12** and **NEM13**
metering files. Implements AEMO MDFF (Meter Data File Format) v2.6.

- O(1) memory — iterate through millions of intervals.
- Pure stdlib core; pandas / PyMySQL are opt-in extras.
- ~2 M readings/sec on the columnar fast path.
- Includes an `aemo-mdff-reader` CLI.

## Install

```bash
pip install aemo-mdff-reader

# optional extras
pip install aemo-mdff-reader[pandas]   # to_dataframe() / parquet
pip install aemo-mdff-reader[mysql]    # SQL persistence
```

## Use

```python
from aemo_mdff_reader import parse

for r in parse("metering.csv"):
    print(r.nmi, r.interval_start, r.value, r.uom)
```

Or as a flat CSV / DataFrame:

```python
from aemo_mdff_reader import parse, write_csv, to_dataframe

write_csv(parse("metering.csv"), "out.csv")     # no pandas
df = to_dataframe("metering.csv")                # needs [pandas]
```

From the command line:

```bash
aemo-mdff-reader metering.csv -o out.csv
aemo-mdff-reader metering.csv --validate                       # spec check
aemo-mdff-reader metering.csv --nmi NMI1234567 --start 2024-01-01 --end 2024-01-31
aemo-mdff-reader manual.csv --records accumulations            # NEM13
```

## Working with the data

Each parsed record is a slots-based class with named attributes plus a
`to_dict()` for JSON / dict pipelines:

```python
for r in parse("metering.csv"):
    payload = r.to_dict()              # {"nmi": "...", "value": 0.12, ...}
    print(r.quality_flag, r.method_flag)  # split of the QMM field, e.g. "S", "52"
```

For aggregation, `aemo_mdff_reader.aggregate` provides streaming helpers:

```python
from aemo_mdff_reader import parse
from aemo_mdff_reader.aggregate import group_by_nmi, daily_totals

for key, group in group_by_nmi(parse("metering.csv")):
    # key = ChannelKey(nmi, register_id, nmi_suffix)
    intervals = list(group)

for day in daily_totals(parse("metering.csv")):
    # day.total, day.interval_count, day.unique_quality_flags
    print(day.nmi, day.interval_date.date(), day.total, day.uom)
```

End-to-end recipes — load + inspect, daily roll-up, filter to pandas,
spec validation — live in [`examples/`](examples/).

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
| Validate against AEMO MDFF v2.6       | `validate_file(src)`          |
| Compute / verify an NMI checksum      | `nmi_checksum`, `validate_nmi`|
| Group readings by NMI / channel       | `aggregate.group_by_nmi(rows)`|
| Roll up to daily totals               | `aggregate.daily_totals(rows)`|
| Convert any record to a plain dict    | `r.to_dict()`                 |

`src` can be a path, a file-like object, an iterable of CSV lines, or
an iterable of pre-split rows. The v1 `NEMReader` facade
(`read_from_file`, `to_dataframe`, `to_csv`) still works.

Each `parse(...)` yields an `IntervalReading` with `nmi`,
`meter_serial_number`, `register_id`, `nmi_suffix`, `uom`,
`interval_length`, `interval_date`, `interval_start`, `interval_end`,
`interval_index`, `value`, `quality_method`, `reason_code`,
`reason_description`, `update_datetime`, `msats_load_datetime`. See
the type stubs (`from aemo_mdff_reader import IntervalReading`) for the
exact signatures.

## Notes

- **Spec**: AEMO Meter Data File Format Specification NEM12 & NEM13,
  **v2.6** (effective 29 September 2024). Records `100`, `200`, `250`,
  `300`, `400`, `500`, `550`, `900` are all surfaced; unknown indicators
  are ignored. Allowed values for quality flags, transaction codes,
  reason codes, units of measure, and direction indicators are exposed
  as constants in `aemo_mdff_reader.spec` for callers that want stricter
  validation than the parser performs.
- **Tolerant**: UTF-8 BOM is consumed silently, LF and CRLF both work,
  and empty interval cells are coerced to `0.0` (use `quality_method`
  to distinguish missing from zero). Datetime fields accept the spec
  forms (`YYYYMMDD`, `YYYYMMDDhhmmss`) and a few common non-spec
  variants (`YYYY-MM-DD`, ISO `YYYY-MM-DDTHH:MM:SS`, with or without a
  `Z` / `±HH:MM` / `±HHMM` timezone suffix — the suffix is stripped
  and parsed datetimes are returned naive). `direction_indicator` on
  250 records passes through whatever the file emits; the spec set is
  `spec.DIRECTION_INDICATORS = {"I", "E"}` but `B` and `N` appear in
  the wild. The parser also accepts non-spec IntervalLengths (1, 60,
  etc.); strict callers should compare against
  `spec.ALLOWED_INTERVAL_LENGTHS` (= `{5, 15, 30}`).
- **Migration from v1**: `NEMReader` still works. The internal
  `aemo_mdff_reader.nemstructure` package is gone — see the API table
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

## Large files

The parser is built to scale to gigabyte-class NEM12 files without
loading them into RAM. Measured peak memory delta on a synthetic
**10.5 M-reading file** (100 NMIs × 365 days × 5-min, 71 MiB CSV),
Python 3.12:

| API                                      | Memory profile | Peak Δ |
| ---------------------------------------- | -------------- | -----: |
| `for r in parse(path): ...`              | streaming      | **1.3 MiB** |
| `daily_totals(parse(path))`              | streaming      | **0 MiB** |
| `write_csv(parse(path), out)`            | streaming      | **0 MiB** |
| `iter_dataframes(path, chunk_size=N)`    | bounded O(N)   | **~30 MiB / 100k** |
| `iter_columns_chunks(path, chunk_size=N)`| bounded O(N)   | **~10 MiB / 100k** |
| `parse_to_columns(path)`                 | full materialise | ~600 MiB |
| `list(parse(path))` / `to_dataframe(path)` / `NEMReader.read_from_file()` | full materialise | ~2.5 GiB |

Rule of thumb: stay on the streaming or chunked APIs for any file
larger than a few hundred MiB. The chunked variants make pandas-based
workflows safe on arbitrarily large inputs:

```python
from aemo_mdff_reader import iter_dataframes

# Process a multi-GiB file 50,000 readings at a time.
for df in iter_dataframes("huge.csv", chunk_size=50_000):
    daily = df.groupby(["NMI", "IntervalDate"])["Value"].sum()
    daily.to_csv("out.csv", mode="a", header=False)
```

The `NEMReader` facade and `to_dataframe(path)` materialise their
inputs by design (so `len(reader)` and `df.iloc[...]` work). Avoid
them for files that won't fit in RAM.

## Development

```bash
git clone https://github.com/Utilified/aemo-mdff-reader.git
cd aemo-mdff-reader
pip install -e .[dev]
pytest
```

CI runs ruff, mypy --strict, the test matrix on Python 3.9 → 3.12 /
Linux / macOS / Windows, `pip-audit`, `bandit`, CodeQL, OpenSSF
Scorecard, and a wheel-install smoke test.

Releases are automated by [release-please](https://github.com/googleapis/release-please)
from [Conventional Commits](https://www.conventionalcommits.org/) on
`main`, then signed with sigstore, attested with SLSA build provenance
and a CycloneDX SBOM, and published to PyPI via Trusted Publishing.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor commit
conventions and the full release flow.

## License

MIT — see [LICENSE](LICENSE).
