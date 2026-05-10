# Contributing

Thanks for your interest in improving nem12-reader. The repository is
small and the bar for contributions is straightforward: a pull request
that passes CI and doesn't regress the public benchmark is welcome.

## Setup

```bash
git clone https://github.com/utilified/nem12-reader.git
cd nem12-reader
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Running the test suite

```bash
pytest -v
pytest --cov=nem12_reader --cov-report=term-missing
```

A small, sanitized NEM12 sample lives at
`tests/fixtures/sample_nem12.csv`. To generate larger synthetic files
for ad-hoc testing or benchmarking:

```bash
python tests/fixtures/generate.py /tmp/big.csv --nmis 4 --days 365 --interval-minutes 5
```

## Performance

`benchmarks/bench_parser.py` is the canonical performance test. Please
run it before and after changes that touch the hot path
(`parser.py::_emit_intervals`, `parse_to_columns`, `to_columns`):

```bash
python benchmarks/bench_parser.py --nmis 4 --days 365 --interval-minutes 5
```

The streaming and columnar fast paths must remain at or above the
current published throughput.

## Code style

- Pure stdlib in the core. **No** new required runtime dependencies.
  Optional features go behind `[project.optional-dependencies]`.
- Type hints on all public symbols.
- Keep `nem12_reader.types` slots-based — per-row allocation is on
  the hot path.

## Reporting issues

Please open an issue with:

1. The Python version and OS.
2. A minimal reproducer (a few NEM12 rows is usually enough).
3. The expected vs actual behaviour.

If you can share a sanitized sample file (no real NMIs / meter
serials), please attach it to the issue.

## Releasing

Maintainers only. Releases are tagged and published to PyPI from the
`main` branch:

```bash
git tag vX.Y.Z
git push --tags
python -m build
twine upload dist/*
```
