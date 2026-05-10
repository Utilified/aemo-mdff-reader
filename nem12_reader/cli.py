"""Command-line interface for nem12-reader.

Installed as the ``nem12-reader`` console script via the project's
``[project.scripts]`` entry in ``pyproject.toml``.

Usage::

    nem12-reader INPUT [-o OUTPUT] [--records intervals|accumulations]
                                   [--format csv|parquet]

If ``OUTPUT`` is omitted, results are written to stdout.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from . import __version__
from .parser import (
    parse,
    parse_accumulations,
    parse_accumulations_to_columns,
    parse_to_columns,
    validate_file,
    write_accumulations_csv,
    write_csv,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nem12-reader",
        description=(
            "Read an AEMO NEM12 / NEM13 file and emit a flat CSV. Streams in O(1) memory."
        ),
    )
    p.add_argument("input", help="Path to the NEM12 / NEM13 input file (CSV).")
    p.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output path. Use '-' (the default) for stdout.",
    )
    p.add_argument(
        "--records",
        choices=("intervals", "accumulations"),
        default="intervals",
        help=(
            "Which record type to emit. 'intervals' = NEM12 300 records "
            "(default), 'accumulations' = NEM13 250 records."
        ),
    )
    p.add_argument(
        "--format",
        choices=("csv", "parquet"),
        default="csv",
        help="Output format. 'parquet' requires pandas + pyarrow.",
    )
    p.add_argument(
        "--validate",
        action="store_true",
        help=(
            "Run structural validation against the AEMO MDFF spec and exit. "
            "Returns 0 if the file is valid, 1 if issues were found."
        ),
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"nem12-reader {__version__}",
    )
    return p


def _emit_parquet(args: argparse.Namespace) -> int:
    try:
        import pandas as pd
    except ImportError:
        print(
            "parquet output requires pandas + pyarrow: pip install nem12-reader[parquet]",
            file=sys.stderr,
        )
        return 2
    if args.records == "accumulations":
        df = pd.DataFrame(parse_accumulations_to_columns(args.input))
    else:
        df = pd.DataFrame(parse_to_columns(args.input))
    df.to_parquet(args.output)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.validate:
        issues = validate_file(args.input)
        if issues:
            for msg in issues:
                print(msg, file=sys.stderr)
            return 1
        print("OK", file=sys.stderr)
        return 0

    if args.format == "parquet":
        return _emit_parquet(args)

    out_target = sys.stdout if args.output == "-" else args.output

    try:
        if args.records == "accumulations":
            write_accumulations_csv(parse_accumulations(args.input), out_target)
        else:
            write_csv(parse(args.input), out_target)
    except BrokenPipeError:
        # Downstream consumer (e.g. ``head``) closed the pipe early —
        # this is normal, not an error.
        try:
            sys.stdout.flush()
        except BrokenPipeError:
            pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
