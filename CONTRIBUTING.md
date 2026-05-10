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
git clone https://github.com/Utilified/aemo-mdff-reader.git
cd aemo-mdff-reader
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest
```

## CI requirements files

`requirements/{dev,lint,build,audit}.txt` are hash-pinned lock files
consumed by CI (`pip install --require-hashes`). They satisfy
Scorecard's `PinnedDependenciesID` and protect CI against a compromised
PyPI mirror. Dependabot refreshes them weekly.

Source `.in` files are committed alongside the locks in `requirements/`.
To regenerate manually after editing them or `pyproject.toml`:

```bash
pip install uv
uv pip compile --generate-hashes --strip-extras --python-version 3.11 --output-file requirements/dev.txt   requirements/dev.in
uv pip compile --generate-hashes --strip-extras --python-version 3.11 --output-file requirements/lint.txt  requirements/lint.in
uv pip compile --generate-hashes --strip-extras --python-version 3.11 --output-file requirements/build.txt requirements/build.in
uv pip compile --generate-hashes --strip-extras --python-version 3.11 --output-file requirements/audit.txt requirements/audit.in
```

`uv` is used over `pip-tools` because its resolver handles the
3.11–3.12 matrix without back-tracking failures, and it emits hashes
for every wheel of each pinned version (so a single lock file works
across the whole CI matrix). The `--python-version 3.11` flag pins
resolution to the lowest supported interpreter so packages whose
latest releases dropped support for it are correctly stepped back
to a compatible version.

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

## Commit messages

Releases are generated automatically from commits using
[release-please](https://github.com/googleapis/release-please), so the
commit subject prefix is load-bearing — it determines whether a release
is cut and what kind of version bump it gets.

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix                             | Effect on next release                 |
| ---------------------------------- | -------------------------------------- |
| `feat: …`                          | minor bump (e.g. 2.0.x → 2.1.0)        |
| `fix: …`                           | patch bump (e.g. 2.0.0 → 2.0.1)        |
| `feat!: …` or `BREAKING CHANGE:` footer | major bump (e.g. 2.x → 3.0.0)     |
| `chore: …` / `docs: …` / `refactor: …` / `style: …` / `test: …` / `ci: …` / `build: …` | no release on its own |
| any commit with `Release-As: x.y.z` footer | forces that exact version    |

Subject line: imperative mood, under 72 chars, lowercase after the
prefix. Examples that work well:

```
feat: stream NEM13 250 records via parse_accumulations
fix: handle CRLF line endings in 300-record payloads
chore: bump CI matrix to include Python 3.13
```

Squash-merge is preferred — the squash commit message becomes the
release-please input, so make it count.

## Reporting issues

Please open an issue with:

1. The Python version and OS.
2. A minimal reproducer (a few NEM12 rows is usually enough).
3. The expected vs actual behaviour.

If you can share a sanitized sample file (no real NMIs / meter
serials), please attach it to the issue.

## Releasing

Releases are automated via [release-please](https://github.com/googleapis/release-please).
Maintainers do not run `git tag` by hand for normal releases.

### Normal flow (Conventional Commits drive it)

1. Land a `feat:` or `fix:` commit on `main` (via squash-merged PR).
2. The `release-please` workflow runs and either opens a new release PR
   titled `chore(main): release X.Y.Z` or updates the existing one.
   The PR auto-bumps `pyproject.toml` and `aemo_mdff_reader/__init__.py`
   (the `# x-release-please-version` annotation in `__init__.py` marks
   the line release-please rewrites) and drafts the `CHANGELOG.md`
   entry from the commit log.
3. Review the release PR. Edit the changelog entry directly on the PR
   if you want to massage wording — release-please will keep your
   edits across reruns. When happy, **squash-merge** it.
4. release-please creates the `vX.Y.Z` git tag on merge.
5. Because tags created by `GITHUB_TOKEN` do not trigger downstream
   tag-push workflows (GitHub anti-recursion guard), `release-please.yml`
   explicitly dispatches `release.yml` for the new tag.
6. `release.yml` runs the publish pipeline:
   build → SLSA build provenance attestation → CycloneDX SBOM +
   attestation → upload artefacts → wait on the `pypi` Environment
   reviewer → sigstore sign → PyPI Trusted Publishing → GitHub Release
   with wheel + sdist + sigstore signatures + SBOM + the in-toto
   provenance bundle (`provenance/aemo_mdff_reader.intoto.jsonl`)
   attached. The provenance file lets external scanners (Scorecard,
   in-toto verifiers) confirm the artefacts were built by this
   workflow without a round-trip to the GitHub attestations API.
7. Approve the deployment in the `pypi` Environment when GitHub
   notifies you. The publish completes; verify at
   https://pypi.org/project/aemo-mdff-reader/ and
   https://github.com/Utilified/aemo-mdff-reader/releases.

### Forcing a release without a feat/fix commit

Two options:

- Add `Release-As: x.y.z` as a commit-message footer on a commit
  landing on `main` (works for `chore:` / `docs:` etc. that wouldn't
  trigger a release on their own).
- Manually trigger the `release-please` workflow via GitHub Actions →
  *release-please* → "Run workflow" (workflow_dispatch).

### Emergency manual release (rare)

`release.yml` still listens on tag-push, so a maintainer can bypass
release-please entirely:

```bash
# Bump version in pyproject.toml AND aemo_mdff_reader/__init__.py
# (preserve the `# x-release-please-version` comment on __init__.py),
# update CHANGELOG.md, then:
git commit -am "release: vX.Y.Z"
git tag vX.Y.Z
git push origin main vX.Y.Z
```

Use only if release-please is broken — otherwise you'll fight it on
the next push.

### One-time infrastructure setup (per project)

Already done for `aemo-mdff-reader`; documented here for posterity.

1. **PyPI Trusted Publishing**: register the project at
   https://pypi.org/manage/account/publishing/ with:
   - PyPI project name: `aemo-mdff-reader`
   - Owner: `Utilified`
   - Repository: `aemo-mdff-reader`
   - Workflow filename: `release.yml`
   - Environment name: `pypi`
2. **GitHub Environment**: in *Settings → Environments*, create an
   environment named `pypi`. Add required reviewers (recommended) and
   restrict the deployment branch policy to `v*` tags.
3. **Repository variable**: set `PYPI_PUBLISH_ENABLED=true` under
   *Settings → Secrets and variables → Actions → Variables*. The
   publish job is gated on this so the workflow runs cleanly while
   Trusted Publishing is being configured (build + sign succeed;
   publish skips).
4. **Workflow permissions**: under *Settings → Actions → General →
   Workflow permissions*, set "Read and write permissions" and tick
   "Allow GitHub Actions to create and approve pull requests" — the
   `release-please` action needs both to open release PRs.

### Local dry run of the build

```bash
python -m build
twine check --strict dist/*
python -m venv /tmp/smoke && /tmp/smoke/bin/pip install dist/*.whl
/tmp/smoke/bin/aemo-mdff-reader --version
```

There is no way to dry-run the publish step — Trusted Publishing only
authenticates a real `release.yml` run on a real tag. The first
release after touching `release.yml` is the de-facto integration test.
