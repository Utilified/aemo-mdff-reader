# AGENTS.md

Pure-stdlib streaming reader for AEMO MDFF **NEM12** (interval) and **NEM13** (accumulation) metering files. Public, MIT-licensed, on PyPI as `aemo-mdff-reader`. Spec target is AEMO MDFF v2.6 (29 September 2024).

## Streaming-first is the whole design

NEM12/NEM13 files can be terabytes of half-hourly readings, so **everything in the public surface yields lazily and stays O(1) in memory**. The buffered APIs (`NEMReader`, `to_dataframe(path)`) are convenience wrappers over the streaming primitives, not the other way round. Never materialise a whole file.

- **`parser.py` is the hot path** and holds every public entry point. Treat `_emit_intervals`, `parse_to_columns` and `to_columns` as performance-critical: benchmark before *and* after any change there:
  ```bash
  python benchmarks/bench_parser.py --nmis 4 --days 365 --interval-minutes 5
  ```
  `parse_to_columns` builds columnar output in a single pass; don't refactor it into row-then-frame.
- **`types.py` row classes must stay `__slots__`-based.** Per-row allocation is on the hot path; a dataclass or plain class breaks the benchmark.
- **`spec.py` is the only file to update when the spec changes.** It holds the v2.6 enumerations (quality flags, transaction codes, reason codes, units of measure). The parser does not enforce enumerations; that is opt-in via `validate_file()` / `--validate`.
- `reader.py`'s `NEMReader` exists only for v1 backward compatibility. New code calls parser functions directly.

## Correctness rules

- **An empty reading cell parses to `None`, never `0.0`.** A missing reading must stay distinguishable from a genuine zero in a billing input. Never coerce `None` to zero anywhere (parser, columnar paths, pandas/parquet, `aggregate`); `daily_totals` skips `None` and counts it in `missing_count`.
- **Malformed input raises `NEM12ParseError`** (a `ValueError` subclass in `parser.py`), naming the offending field and value. Never silently truncate, skip or default a bad row, and never let a raw `ValueError` escape the parse boundary. The one tolerance: an unparseable 100-record DateTime is accepted outside `validate_file()` (`_parse_header(strict=True)` is used only there).

## Constraints that aren't visible in the code

- **Pure stdlib in the core. Do not add a required runtime dependency.** The only extras are `[pandas]` and `[parquet]`; optional imports happen **lazily inside functions**, never at module top level.
- **Don't convert `Union`/`Optional`/`Dict` hints to PEP 604/585 syntax opportunistically.** The `UP006`/`UP007`/`UP035`/`UP045` ignores in `pyproject.toml` keep that migration a separate, deliberate change.
- **Type hints on every public symbol.** CI runs `mypy --strict` on `aemo_mdff_reader/`.
- **Tests use synthetic data only.** NMIs, meter serials and participant codes in fixtures must be obviously fake (`NMI1234567`, `METER000001`). Never commit real AEMO metering data. Use `tests/fixtures/generate.py` for synthetic files.

Coverage gate is 90% (`fail_under`). Before committing: `ruff check . && ruff format --check . && mypy && pytest`.

CI installs from hash-pinned locks in `requirements/*.txt`. Edit the `.in` file and regenerate with the `uv pip compile` commands in [CONTRIBUTING.md](CONTRIBUTING.md); never hand-edit a `.txt` lock.

## Commits, PRs and releases

release-please drives releases; never bump a version or push a tag by hand. The full process is in [CONTRIBUTING.md](CONTRIBUTING.md).

- **PR titles must be Conventional Commits** (`pr-title.yml` checks them), because `main` is squash-merge only and the squash subject is what release-please reads. `feat:` → minor, `fix:` → patch, `feat!:`/`BREAKING CHANGE:` → major; `chore:`/`docs:`/`refactor:`/`style:`/`test:`/`ci:`/`build:` release nothing. A `Release-As: x.y.z` footer forces a version.
- `main` rules: changes land via PR, squash-merge only, no force-push or branch deletion.
- The version lives in `pyproject.toml`, `.release-please-manifest.json` and `aemo_mdff_reader/__init__.py`. The `# x-release-please-version` trailing comment on the `__init__.py` line is how release-please finds it: never remove or move it.

## Workflow gotchas

- **`release-please.yml` dispatches `release.yml` explicitly** (`gh workflow run --ref <tag> --repo ...`), because tags created by the default `GITHUB_TOKEN` don't trigger tag-push workflows. `--repo` is required because that job has no checkout step.
- **`release.yml` writes the SBOM to `sbom/`, not `dist/`**, or the PyPI publish action rejects the non-wheel file. Keep the `mkdir -p sbom` step: the SBOM action doesn't create the directory.
- Publishing is gated on `vars.PYPI_PUBLISH_ENABLED == 'true'` and runs in the `pypi` GitHub Environment.
- **Third-party actions are SHA-pinned with the tag as a trailing comment** (`actions/checkout@<sha> # v6`). Dependabot only updates them while that comment stays on the same line. Resolve a new SHA with `gh api repos/<owner>/<repo>/commits/<tag>`.

Local release dry-run: `python -m build && twine check --strict dist/*`.
