# Contributing

Thanks for your interest in improving aemo-mdff-reader. The repository
is small and the bar for contributions is straightforward: a pull
request that passes CI and doesn't regress the public benchmark is
welcome.

Naming: everything (GitHub repo `Utilified/aemo-mdff-reader`, PyPI
distribution `aemo-mdff-reader`, Python import `aemo_mdff_reader`,
CLI `aemo-mdff-reader`) is consistently named after the AEMO spec —
MDFF, the Meter Data File Format that covers both NEM12 (interval) and
NEM13 (accumulation) formats. GitHub serves redirects from the
previous `Utilified/nem12-reader` repo URL so existing git pins
continue to work; v1 callers importing `from nem12_reader …` need to
update to `from aemo_mdff_reader …`.

## Setup

```bash
git clone https://github.com/utilified/aemo-mdff-reader.git
cd aemo-mdff-reader
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Running the test suite

```bash
pytest -v
pytest --cov=aemo_mdff_reader --cov-report=term-missing
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
- Keep `aemo_mdff_reader.types` slots-based — per-row allocation is on
  the hot path.

## Reporting issues

Please open an issue with:

1. The Python version and OS.
2. A minimal reproducer (a few NEM12 rows is usually enough).
3. The expected vs actual behaviour.

If you can share a sanitized sample file (no real NMIs / meter
serials), please attach it to the issue.

## Releasing

Maintainers only. Releases are tagged and pushed to GitHub; the
`Release` workflow then builds, signs (sigstore), publishes to PyPI
(via Trusted Publishing), and attaches signatures to the GitHub Release.

### One-time setup (per project)

Before the first release, configure these on PyPI / GitHub:

1. **PyPI Trusted Publishing**: register the project at
   https://pypi.org/manage/account/publishing/ with:
   - PyPI project name: `aemo-mdff-reader`
   - Owner: `utilified`
   - Repository: `aemo-mdff-reader`
   - Workflow filename: `release.yml`
   - Environment name: `pypi`
2. **GitHub Environment**: in *Settings → Environments*, create an
   environment named `pypi`. Add required reviewers if you want
   manual approval before publish (recommended for the first few
   releases). Without this environment, the publish job will fail with
   a confusing "environment not found" error.

### Cutting a release

```bash
# Bump version in pyproject.toml AND aemo_mdff_reader/__init__.py.
# Update CHANGELOG.md with the new section.
git commit -am "release: vX.Y.Z"
git tag vX.Y.Z
git push origin main vX.Y.Z
```

The `Release` workflow takes over from here. Verify the published
artefact at https://pypi.org/project/aemo-mdff-reader/ and the
GitHub Release at https://github.com/utilified/aemo-mdff-reader/releases.

### Local dry run

```bash
python -m build
twine check --strict dist/*
python -m venv /tmp/smoke && /tmp/smoke/bin/pip install dist/*.whl
/tmp/smoke/bin/aemo-mdff-reader --version
```
