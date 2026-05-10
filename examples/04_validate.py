"""Run structural validation against a NEM12 / NEM13 file.

Equivalent to ``aemo-mdff-reader path/to/file.csv --validate`` but shown
here as a programmatic example for callers that want to fold spec
checks into a larger pipeline.

Usage:  python examples/04_validate.py path/to/file.csv
"""

from __future__ import annotations

import sys

from aemo_mdff_reader import spec, validate_file


def main(path: str) -> int:
    print(
        f"Validating against AEMO MDFF v{spec.SPEC_VERSION} (effective {spec.SPEC_EFFECTIVE_DATE}):"
    )
    issues = validate_file(path)
    if not issues:
        print("  OK — no structural issues found.")
        return 0
    for msg in issues:
        print(f"  ✗ {msg}")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
