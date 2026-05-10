# Changelog

All notable changes are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1 adoption notice).
- GitHub issue forms for bug reports and feature requests, plus a
  pull request template.
- CodeQL workflow for static analysis on push / PR / schedule.
- OpenSSF Scorecard workflow for supply-chain posture reporting.

### Changed

- GitHub Actions across all workflows pinned to commit SHAs (managed
  by Dependabot) for supply-chain hardening.

### Fixed

- GitHub org casing in repository URLs (`utilified` → `Utilified`).

## [2.0.1] — 2026-05-10

The 2.0.0 tag was cut before the project was renamed to
`aemo-mdff-reader`. 2.0.1 is the first version published under the new
name end-to-end. Source semantics are unchanged — this release exists
to give consumers a single stable tag matching the
`aemo_mdff_reader` import path and the `aemo-mdff-reader` PyPI dist
+ CLI command.

### Changed

- **Project renamed end-to-end** to `aemo-mdff-reader`: GitHub repo
  `Utilified/aemo-mdff-reader`, PyPI distribution `aemo-mdff-reader`,
  Python import `aemo_mdff_reader`, CLI command `aemo-mdff-reader`.
  v1 callers using `from nem12_reader import …` must update their
  imports; any references to the `nem12-reader` CLI command must be
  updated. GitHub redirects the previous repo URL so existing git
  pins (`git@github.com:Utilified/nem12-reader.git`) keep resolving.

### Tooling

- Bumped GitHub Actions used in `ci.yml` / `release.yml` to their
  current major versions: `actions/setup-python@v6`,
  `actions/upload-artifact@v7`, `actions/download-artifact@v8`,
  `softprops/action-gh-release@v3` (Node 24 runtime),
  `sigstore/gh-action-sigstore-python@v3.3.0`.
- The release workflow's PyPI publish step is now gated on
  `vars.PYPI_PUBLISH_ENABLED == 'true'`, so tag pushes run cleanly
  before Trusted Publishing is configured (build + sign succeed;
  publish + GitHub-release jobs skip).
- Repository description, homepage, and topic tags configured for
  PyPI / GitHub discoverability.

## [2.0.0] — 2026-05-10

### Highlights

- **Renamed to `aemo-mdff-reader` end-to-end.** v1 shipped under
  `nem12-reader` (GitHub repo, PyPI distribution, Python import, and
  CLI command). v2 unifies all four surfaces under
  `aemo-mdff-reader` / `aemo_mdff_reader` — the AEMO spec name (MDFF,
  Meter Data File Format) covers both NEM12 (interval) and NEM13
  (accumulation) data and disambiguates the project from the
  unrelated `nem-reader` package on PyPI. GitHub redirects the
  previous repo URL so existing git pins
  (`git@github.com:Utilified/nem12-reader.git`) continue to resolve.
  Source consumers must update their imports
  (`from nem12_reader import …` → `from aemo_mdff_reader import …`)
  and any references to the `nem12-reader` CLI command.
- **Spec target: AEMO MDFF v2.6** (effective 29 September 2024).
  Previous v1.x of this package targeted MDFF v1.02 (2017). All
  record-type schemas, allowed values, and reason-code descriptions
  are aligned to v2.6 — including the v2.6 reason codes added by the
  ICF_054 substitution-type review (codes 100–109) and the v2.6
  designation of obsolete reason codes (Appendix F). The full set is
  exposed as constants in the new `aemo_mdff_reader.spec` module.
- **Zero required dependencies**: pandas, PyMySQL, wrapt, six, tomli,
  pytz, python-dateutil are no longer required. pandas / PyMySQL are
  available as opt-in extras (`pip install aemo-mdff-reader[pandas]`,
  `[mysql]`).
- **Streaming parser** (`aemo_mdff_reader.parse`): O(1) memory, works on
  arbitrarily large files.
- **Columnar fast path** (`parse_to_columns`, `to_dataframe(path)`):
  ~7× faster than the v1 `read_from_file` + `to_dataframe` flow.
- **Full NEM13 (250) accumulation support**: `parse_accumulations`,
  `to_accumulations_dataframe`, `write_accumulations_csv`. `parse_all`
  emits both NEM12 and NEM13 records in file order.
- **Full record-type coverage**: `parse_events()` (400 quality/event
  rows), `parse_b2b()` (500 NEM12 + 550 NEM13 transaction details).
- **Spec-conformance utilities**: `nmi_checksum()`, `validate_nmi()`,
  `validate_file()` plus a `aemo-mdff-reader --validate` CLI flag.
- **CLI** (`aemo-mdff-reader`): convert NEM12 / NEM13 → flat CSV / parquet
  from the command line. Was previously documented but not implemented.
  `--records intervals|accumulations` selects the record type;
  `--validate` runs structural checks against the AEMO MDFF spec.

### Added

- `aemo_mdff_reader.parse(source)` — generator-based streaming parser
  (NEM12 300 records).
- `aemo_mdff_reader.parse_to_columns(source)` — single-pass columnar
  parse without per-cell row-object allocation.
- `aemo_mdff_reader.parse_header(source)` — header-only fast read.
- `aemo_mdff_reader.parse_accumulations(source)` — NEM13 250 record
  streaming parser.
- `aemo_mdff_reader.parse_accumulations_to_columns(source)` — columnar
  NEM13 fast path.
- `aemo_mdff_reader.parse_all(source)` — unified iterator yielding both
  300 and 250 records in file order.
- `aemo_mdff_reader.to_dataframe(source)` and
  `to_accumulations_dataframe(source)` — pandas DataFrame builders.
- `aemo_mdff_reader.write_csv(...)` and `write_accumulations_csv(...)` —
  flat-CSV writers that work without pandas.
- `aemo_mdff_reader.types` — slots-based `Header`, `NMIDetails`,
  `IntervalReading`, `IntervalEvent`, `AccumulationReading` classes.
- `aemo_mdff_reader.cli.main` — `aemo-mdff-reader` console script with
  `--records intervals|accumulations` and `--format csv|parquet`.
- `pyproject.toml` (PEP 621) with full metadata, classifiers, and
  optional extras (`pandas`, `parquet`, `mysql`, `dev`).
- `mypy --strict` configuration; the public `aemo_mdff_reader` surface
  is fully typed and passes `mypy --strict`.
- `ruff` lint + format configuration.
- `LICENSE` file (MIT).
- `tests/` — 55-test pytest suite covering parser, edge cases,
  datetime variants, CLI, NEM13, and lazy SQL imports.
- `benchmarks/bench_parser.py` — repeatable performance benchmark.
- GitHub Actions:
  - CI matrix (Python 3.8 → 3.12, Linux/macOS/Windows).
  - `ruff` lint job.
  - `mypy --strict` job.
  - Build job with `twine check --strict` and wheel-install smoke.
  - Release workflow (`release.yml`) — publishes to PyPI on tag via
    Trusted Publishing.
- `dependabot.yml` — weekly bumps for GitHub Actions and pip.
- `.pre-commit-config.yaml` — local lint + format + mypy hooks.

### Changed

- `NEMReader().to_dataframe()` now uses the columnar fast path when
  the source filename is known. Output schema clarifies interval
  start/end timestamps and adds an explicit Suffix column.
- `aemo_mdff_reader.sql` no longer eagerly imports `pymysql`; the
  dependency is only loaded when `Storer` is instantiated.

### Removed

- `aemo_mdff_reader.nemstructure` package (Header / NMIData / IntervalData
  abstractions and the dynamically-built `NEMField` schema). The new
  `aemo_mdff_reader.types` module replaces this surface with simpler,
  faster slots classes.
- Broken `aemo_mdff_reader.nemstructure.nem13` and `enem12` modules,
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
