# Security policy

## Reporting a vulnerability

If you believe you've found a security issue in `aemo-mdff-reader`, please
report it **privately** rather than opening a public GitHub issue. The
preferred channel is GitHub's [private vulnerability reporting form](https://github.com/Utilified/aemo-mdff-reader/security/advisories/new),
which lets us track triage and disclosure without exposing the bug
publicly until a fix is available.

If for any reason that form isn't usable, email the maintainers at
**security@utilified.com** with:

- A short description of the issue and its impact.
- A minimal reproducer (a few NEM12 / NEM13 rows is usually enough —
  please **do not include real NMIs or meter serials**, sanitise first).
- The version you tested against (`pip show aemo-mdff-reader` or git ref).

We aim to acknowledge reports within **5 business days** and to provide
a fix or mitigation plan within **14 days**, depending on severity.

## Scope

In scope:

- The `aemo_mdff_reader` Python package and its `aemo-mdff-reader` CLI.
- The release pipeline (`.github/workflows/release.yml`) and the
  signed artefacts it publishes.

Out of scope:

- Vulnerabilities in upstream Python, GitHub Actions, or any optional
  dependency (`pandas`, `pyarrow`, `pymysql`). Please report those to
  their respective maintainers.
- The legacy `aemo_mdff_reader.sql` subpackage is opt-in (`pip install
  aemo-mdff-reader[mysql]`); SQL-injection findings there are
  acknowledged but lower priority — the package is intended for
  controlled internal pipelines, not user-facing query handling.

## Supported versions

Security fixes are issued only for the current minor release line.

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | ✅                  |
| 2.x earlier | ❌ (use latest 2.0.x) |
| 1.x     | ❌ (unsupported)    |

## Disclosure

We follow coordinated disclosure: once a fix is available, we'll
publish a GitHub Security Advisory describing the issue, affected
versions, and mitigations. Reporters are credited in the advisory
unless they request otherwise.
