"""Command-line interface for aemo-mdff-reader.

Installed as the ``aemo-mdff-reader`` console script via the project's
``[project.scripts]`` entry in ``pyproject.toml``.

Usage::

    aemo-mdff-reader INPUT [-o OUTPUT] [--records intervals|accumulations]
                                   [--format csv|parquet]
                                   [--nmi NMI [--nmi NMI ...]]
                                   [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                   [--validate]

If ``OUTPUT`` is omitted, results are written to stdout.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from typing import Iterable, Iterator, Optional, Sequence

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
from .types import AccumulationReading, IntervalReading


def _iso_date(value: str) -> date:
    """Parse a YYYY-MM-DD argparse value, raising ArgumentTypeError on bad input."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD date, got {value!r}") from exc


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aemo-mdff-reader",
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
        "--nmi",
        action="append",
        default=None,
        metavar="NMI",
        help=(
            "Restrict output to the given NMI. Repeat the flag to keep "
            "more than one (e.g. --nmi A --nmi B). Default: all NMIs."
        ),
    )
    p.add_argument(
        "--start",
        type=_iso_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="Drop rows whose interval / current-read date is before this date.",
    )
    p.add_argument(
        "--end",
        type=_iso_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="Drop rows whose interval / current-read date is after this date.",
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
        version=f"aemo-mdff-reader {__version__}",
    )
    return p


def _filter_intervals(
    readings: Iterable[IntervalReading],
    *,
    nmis: Optional[Sequence[str]],
    start: Optional[date],
    end: Optional[date],
) -> Iterator[IntervalReading]:
    nmi_set = set(nmis) if nmis else None
    for r in readings:
        if nmi_set is not None and r.nmi not in nmi_set:
            continue
        d = r.interval_date.date()
        if start is not None and d < start:
            continue
        if end is not None and d > end:
            continue
        yield r


def _filter_accumulations(
    readings: Iterable[AccumulationReading],
    *,
    nmis: Optional[Sequence[str]],
    start: Optional[date],
    end: Optional[date],
) -> Iterator[AccumulationReading]:
    nmi_set = set(nmis) if nmis else None
    for r in readings:
        if nmi_set is not None and r.nmi not in nmi_set:
            continue
        if r.current_register_read_datetime is not None:
            d = r.current_register_read_datetime.date()
            if start is not None and d < start:
                continue
            if end is not None and d > end:
                continue
        yield r


def _emit_parquet(args: argparse.Namespace) -> int:
    try:
        import pandas as pd
    except ImportError:
        print(
            "parquet output requires pandas + pyarrow: pip install aemo-mdff-reader[parquet]",
            file=sys.stderr,
        )
        return 2
    if args.records == "accumulations":
        cols = parse_accumulations_to_columns(args.input)
        df = pd.DataFrame(cols)
    else:
        cols = parse_to_columns(args.input)
        df = pd.DataFrame(cols)

    # Apply --nmi / --start / --end filters in-DataFrame so the parquet
    # output matches what the streaming CSV path would emit.
    if args.nmi:
        df = df[df["NMI"].isin(args.nmi)]
    if args.records == "accumulations":
        date_col = "CurrentRegisterReadDatetime"
    else:
        date_col = "IntervalDate"
    if args.start is not None:
        df = df[df[date_col] >= pd.Timestamp(args.start)]
    if args.end is not None:
        df = df[df[date_col] <= pd.Timestamp(args.end)]

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
            acc_stream = _filter_accumulations(
                parse_accumulations(args.input),
                nmis=args.nmi,
                start=args.start,
                end=args.end,
            )
            write_accumulations_csv(acc_stream, out_target)
        else:
            int_stream = _filter_intervals(
                parse(args.input),
                nmis=args.nmi,
                start=args.start,
                end=args.end,
            )
            write_csv(int_stream, out_target)
    except BrokenPipeError:
        # Downstream consumer (e.g. ``head``) closed the pipe early —
        # this is normal, not an error.
        try:
            sys.stdout.flush()
        except BrokenPipeError:
            # Pipe is already gone; nothing to flush.
            pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
