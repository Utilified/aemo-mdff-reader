"""Command-line interface for nem12-reader.

Installed as the ``nem12-reader`` console script via the project's
``[project.scripts]`` entry in ``pyproject.toml``.

Usage::

    nem12-reader INPUT [-o OUTPUT] [--format csv|parquet]

If ``OUTPUT`` is omitted, results are written to stdout.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from . import __version__
from .parser import parse, write_csv


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nem12-reader",
        description=(
            "Read an AEMO NEM12 file and emit a flat CSV (one row per interval). "
            "Streams in O(1) memory."
        ),
    )
    p.add_argument("input", help="Path to the NEM12 input file (CSV).")
    p.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output path. Use '-' (the default) for stdout.",
    )
    p.add_argument(
        "--format",
        choices=("csv", "parquet"),
        default="csv",
        help="Output format. 'parquet' requires pandas + pyarrow.",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"nem12-reader {__version__}",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    readings = parse(args.input)

    if args.format == "parquet":
        try:
            import pandas as pd  # noqa: WPS433
        except ImportError:
            print(
                "parquet output requires pandas + pyarrow: "
                "pip install nem12-reader[pandas]",
                file=sys.stderr,
            )
            return 2
        from .parser import to_columns

        df = pd.DataFrame(to_columns(readings))
        df.to_parquet(args.output)
        return 0

    if args.output == "-":
        write_csv(readings, sys.stdout)
    else:
        write_csv(readings, args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
