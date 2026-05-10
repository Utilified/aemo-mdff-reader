# nem12-reader

[![CI](https://github.com/utilified/nem12-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/utilified/nem12-reader/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/nem12-reader.svg)](https://pypi.org/project/nem12-reader/)
[![Python versions](https://img.shields.io/pypi/pyversions/nem12-reader.svg)](https://pypi.org/project/nem12-reader/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A fast, **zero-dependency** streaming reader for AEMO NEM12 / NEM13 metering
files. Designed for retailers, distributors, and analysts working with
Australian energy interval data.

- **Streaming** — O(1) memory; iterate through millions of intervals without
  loading the file into RAM.
- **Zero required dependencies** — pure stdlib (`csv`, `datetime`).
  pandas / PyMySQL are opt-in extras.
- **Fast** — ~2 M interval readings/sec on the columnar fast path; ~7×
  faster than the previous tree-based implementation.
- **Typed** — slots-based data classes with type hints throughout.
- **CLI included** — convert NEM12 to flat CSV in one command.

## Installation

```bash
pip install nem12-reader
```

Optional extras:

```bash
pip install nem12-reader[pandas]   # for to_dataframe() / parquet output
pip install nem12-reader[parquet]  # pandas + pyarrow
pip install nem12-reader[mysql]    # SQL persistence (Storer)
```

## Quick start

### Streaming API — NEM12 interval data (recommended)

```python
from nem12_reader import parse

for reading in parse("metering.csv"):
    print(reading.nmi, reading.interval_start, reading.value, reading.uom)
```

`parse()` returns a generator of `IntervalReading` objects (one per
interval cell of a 300 record). Memory is O(1) in file size, so you
can process arbitrarily large files.

### Streaming API — NEM13 accumulation data

```python
from nem12_reader import parse_accumulations

for read in parse_accumulations("manual_reads.csv"):
    print(
        read.nmi, read.register_id,
        read.previous_register_read, read.current_register_read,
        read.quantity, read.uom,
    )
```

`parse_accumulations()` yields `AccumulationReading` objects (one per
NEM13 250 record). For files mixing NEM12 (300) and NEM13 (250) rows,
use `parse_all()` which yields both record types in file order.

### Bulk to pandas DataFrames

```python
from nem12_reader import to_dataframe, to_accumulations_dataframe

intervals    = to_dataframe("metering.csv")              # NEM12 300 records
accumulations = to_accumulations_dataframe("manual.csv") # NEM13 250 records
```

Both paths use the columnar fast-path internally.

### Bulk to flat CSVs (no pandas required)

```python
from nem12_reader import (
    parse, parse_accumulations, write_csv, write_accumulations_csv,
)

write_csv(parse("metering.csv"), "intervals.csv")
write_accumulations_csv(parse_accumulations("manual.csv"), "accumulations.csv")
```

### Quality / event flags (400 records)

```python
from nem12_reader import parse_events

for evt in parse_events("metering.csv"):
    print(evt.nmi, evt.interval_date, evt.start_interval,
          evt.end_interval, evt.quality_method)
```

### B2B transaction details (500 / 550 records)

```python
from nem12_reader import parse_b2b

for b in parse_b2b("metering.csv"):
    if b.record_kind == "500":
        print(b.trans_code, b.ret_service_order, b.read_datetime)
    else:  # "550" (NEM13)
        print(b.previous_trans_code, b.current_trans_code)
```

### Validation

```python
from nem12_reader import nmi_checksum, validate_nmi, validate_file

nmi_checksum("NMI1234567")          # -> int (0-9), AEMO NMI checksum digit
validate_nmi("NMI1234567")          # -> True (structural check)
validate_nmi("NMI1234567", "2")     # -> True if "2" matches the checksum

issues = validate_file("metering.csv")  # list[str], empty if file is valid
```

### CLI

```bash
nem12-reader metering.csv -o out.csv
nem12-reader metering.csv > out.csv                          # stdout
nem12-reader metering.csv -o out.parquet --format parquet
nem12-reader manual.csv --records accumulations -o acc.csv   # NEM13
nem12-reader metering.csv --validate                         # spec check
```

### Backward-compatible facade

If you depend on the v1 API:

```python
from nem12_reader import NEMReader

reader = NEMReader()
reader.read_from_file("metering.csv")
df = reader.to_dataframe()
reader.to_csv("out.csv")
```

## Output schema

Each `IntervalReading` corresponds to a single interval cell within a 300
record:

| Field                 | Type             | Description                          |
| --------------------- | ---------------- | ------------------------------------ |
| `nmi`                 | str              | National Metering Identifier         |
| `meter_serial_number` | str              | Meter serial                         |
| `register_id`         | str              | Register / channel ID                |
| `nmi_suffix`          | str              | NMI suffix                           |
| `uom`                 | str              | Unit of measure (e.g. KWH, KVARH)    |
| `interval_length`     | int              | Interval length in minutes           |
| `interval_date`       | datetime         | Date of the 300 row                  |
| `interval_start`      | datetime         | Start of the interval                |
| `interval_end`        | datetime         | End of the interval                  |
| `interval_index`      | int              | 1-based index within the day         |
| `value`               | float            | Reading                              |
| `quality_method`      | str              | Quality flag (A, S, F, V, N, E)      |
| `reason_code`         | int \| None      | Reason code, if provided             |
| `reason_description`  | str              | Free-text description                |
| `update_datetime`     | datetime \| None | Update datetime                      |
| `msats_load_datetime` | datetime \| None | MSATS load datetime                  |

## Performance

Single-thread, Python 3.11, 4 NMIs × 365 days × 5-minute intervals
(420,480 readings, 2.8 MiB CSV):

| Operation                                  |    Time | Throughput        |
| ------------------------------------------ | ------: | ----------------- |
| `for r in parse(path): ...` (streaming)    | ~0.45 s | 0.9 M readings/s  |
| `parse_to_columns(path)` (fast path)       | ~0.21 s | 2.0 M readings/s  |
| `to_dataframe(path)` (pandas, fast path)   | ~0.76 s |                   |
| _v1 `NEMReader().read_from_file()`_        | _~0.74 s_ | _baseline_      |
| _v1 `read_from_file()` + `to_dataframe()`_ | _~2.03 s_ | _baseline_      |

End-to-end **~2.7× faster** with **O(1) memory** and **zero required
dependencies** (was: pandas, numpy, PyMySQL, wrapt, six, tomli, pytz,
python-dateutil — all required by v1).

Run the bench yourself:

```bash
python benchmarks/bench_parser.py --nmis 4 --days 365 --interval-minutes 5
```

## Specification

Implements AEMO Meter Data File Format (MDFF) Specification — NEM12 and
NEM13. Reference:

- https://www.aemo.com.au/-/media/files/electricity/nem/retail_and_metering/metering-procedures/2017/mdff_specification_nem12_nem13_final_v102.pdf

Supported records:

| Indicator | Record                   | Streaming API                                      |
| --------- | ------------------------ | -------------------------------------------------- |
| `100`     | Header                   | `parse_header()`                                   |
| `200`     | NMI / channel details    | parent context for 300 / 400 rows                  |
| `250`     | NMI accumulation (NEM13) | `parse_accumulations()`                            |
| `300`     | Interval data (NEM12)    | `parse()`                                          |
| `400`     | Interval event           | `parse_events()` → `IntervalEvent`                 |
| `500`     | B2B details              | `parse_b2b()` → `B2BDetails(record_kind="500")`    |
| `550`     | Accumulation B2B (NEM13) | `parse_b2b()` → `B2BDetails(record_kind="550")`    |
| `900`     | End of file              | terminates iteration                               |

`parse_all()` emits 300 and 250 records together in file order for mixed
NEM12/NEM13 inputs. Use `validate_file()` for a fast structural
conformance check (presence of 100/900, 300 rows under a 200, NMI
structural validity, 250 row field count).

## Quality, type-checking, and CI

The package ships with:

- **CI matrix** across Python 3.8 → 3.12 on Linux, macOS, and Windows.
- **`mypy --strict`** check on the public `nem12_reader` surface.
- **`ruff`** lint + format gate.
- **`pytest --cov`** with a 90% coverage floor (`tool.coverage.fail_under`).
- **`twine check --strict`** plus a wheel-install + `nem12-reader --version`
  smoke test on every PR.
- **`pip-audit`** for dependency CVEs and **`bandit`** for static
  security analysis on every PR.
- **PyPI publish on tag** via Trusted Publishing, with **sigstore**
  signatures attached to the GitHub Release
  (`.github/workflows/release.yml`).
- **Dependabot** for GitHub Actions and pip dependencies.
- **Pre-commit** config for local development (`pre-commit install`).

## Migration from v1

- All required dependencies have been dropped from the core. `pandas` is
  now an extra (`pip install nem12-reader[pandas]`).
- `NEMReader().to_dataframe()` and `to_csv()` continue to work; the
  output schema has been clarified (separate `IntervalStart` /
  `IntervalEnd` timestamps, explicit `Suffix` column).
- The internal `nem12_reader.nemstructure` package has been removed.
  Replace `from nem12_reader.nemstructure...` with
  `from nem12_reader import IntervalReading, NMIDetails, Header`.
- Use `parse()` / `parse_to_columns()` for new code — they are an order
  of magnitude faster on large files and stream in O(1) memory.

## Development

```bash
git clone https://github.com/utilified/nem12-reader.git
cd nem12-reader
pip install -e .[dev]
pytest
```

## License

MIT — see [LICENSE](LICENSE).
