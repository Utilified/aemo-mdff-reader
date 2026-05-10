# Changelog

All notable changes are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/).

## [2.0.0] — 2026-05-10

### Highlights

- **Zero required dependencies**: pandas, PyMySQL, wrapt, six, tomli,
  pytz, python-dateutil are no longer required. pandas / PyMySQL are
  available as opt-in extras (`pip install nem12-reader[pandas]`,
  `[mysql]`).
- **Streaming parser** (`nem12_reader.parse`): O(1) memory, works on
  arbitrarily large files.
- **Columnar fast path** (`parse_to_columns`, `to_dataframe(path)`):
  ~7× faster than the v1 `read_from_file` + `to_dataframe` flow.
- **CLI** (`nem12-reader`): convert NEM12 → flat CSV / parquet from
  the command line. Was previously documented but not implemented.

### Added

- `nem12_reader.parse(source)` — generator-based streaming parser.
- `nem12_reader.parse_to_columns(source)` — single-pass columnar
  parse without per-cell row-object allocation.
- `nem12_reader.parse_header(source)` — header-only fast read.
- `nem12_reader.write_csv(readings, output)` — flat-CSV writer that
  works without pandas.
- `nem12_reader.types` — slots-based `Header`, `NMIDetails`,
  `IntervalReading`, `IntervalEvent` data classes.
- `nem12_reader.cli.main` — `nem12-reader` console script.
- `pyproject.toml` (PEP 621) with full metadata, classifiers, and
  optional extras.
- `LICENSE` file (MIT).
- `tests/` — 20-test pytest suite with sanitized fixture.
- `benchmarks/bench_parser.py` — repeatable performance benchmark.
- GitHub Actions CI matrix (Python 3.8 → 3.12, Linux/macOS/Windows).

### Changed

- `NEMReader().to_dataframe()` now uses the columnar fast path when
  the source filename is known. Output schema clarifies interval
  start/end timestamps and adds an explicit Suffix column.
- `nem12_reader.sql` no longer eagerly imports `pymysql`; the
  dependency is only loaded when `Storer` is instantiated.

### Removed

- `nem12_reader.nemstructure` package (Header / NMIData / IntervalData
  abstractions and the dynamically-built `NEMField` schema). The new
  `nem12_reader.types` module replaces this surface with simpler,
  faster slots classes.
- Broken `nem12_reader.nemstructure.nem13` and `enem12` modules,
  which called `Record.__init__(...)` with arguments the base class
  never accepted.
- Dead `requirements.txt` pins for `numpy`, `wrapt`, `six`, `tomli`,
  `python-dateutil`, `pytz`. None were actually used in the codebase.
- The unsanitized `test.csv` sample (contained a real NMI / meter
  serial). Replaced with a synthesized fixture under
  `tests/fixtures/sample_nem12.csv` and a generator script.

### Fixed

- Quadratic-time row consumption in the legacy parser
  (`array = array[1:]` in a hot loop) that scaled poorly on
  large files.
- Per-`IntervalData`-row construction of ~289 `NEMField` objects
  for 5-minute reads (eliminated entirely; schema is fixed in code).
- Eager pandas import on package load.

## [1.0.1] — 2024

Initial public versions. See git history for detailed changes.
