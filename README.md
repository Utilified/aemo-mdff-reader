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

### Streaming API (recommended)

```python
from nem12_reader import parse

for reading in parse("metering.csv"):
    print(reading.nmi, reading.interval_start, reading.value, reading.uom)
```

`parse()` returns a generator of `IntervalReading` objects. Memory is
O(1) in file size, so you can process arbitrarily large files.

### Bulk to a pandas DataFrame

```python
from nem12_reader import to_dataframe

df = to_dataframe("metering.csv")          # columnar fast path
df = df[df["NMI"] == "NMI1234567"]
```

### Bulk to a flat CSV (no pandas required)

```python
from nem12_reader import parse, write_csv

write_csv(parse("metering.csv"), "out.csv")
```

### CLI

```bash
nem12-reader metering.csv -o out.csv
nem12-reader metering.csv > out.csv          # stdout
nem12-reader metering.csv -o out.parquet --format parquet
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

Supported records: `100` (header), `200` (NMI details), `300` (interval
data), `400` (interval events), `900` (end). `500` (B2B details) rows are
recognised and skipped by the streaming reader.

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
