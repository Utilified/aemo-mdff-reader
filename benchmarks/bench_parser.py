"""Micro-benchmark: streaming parser vs the legacy tree-based reader.

This script generates a synthetic NEM12 file in a temp directory and
times three operations:

  1. ``parse(path)``                  — streaming, pure-stdlib
  2. ``NEMReader().read_from_file()`` — buffered facade (uses parse internally)
  3. ``to_dataframe(parse(path))``    — pandas DataFrame, columnar build

Run with::

    python benchmarks/bench_parser.py --nmis 4 --days 365 --interval-minutes 5
"""

from __future__ import annotations

import argparse
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from nem12_reader import NEMReader, parse, parse_to_columns, to_columns


@contextmanager
def _timed(label: str):
    t = time.perf_counter()
    yield lambda: time.perf_counter() - t
    elapsed = time.perf_counter() - t
    print(f"  {label:<32} {elapsed*1000:>8.1f} ms")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--nmis", type=int, default=4)
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--interval-minutes", type=int, default=5)
    args = p.parse_args()

    # Ensure local tests/fixtures generator is on path.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests" / "fixtures"))
    from generate import generate  # type: ignore

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bench.csv"
        with open(path, "w", newline="") as f:
            n_rows = generate(
                f,
                nmis=args.nmis,
                days=args.days,
                interval_minutes=args.interval_minutes,
            )
        size_mb = os.path.getsize(path) / 1024 / 1024
        intervals_per_day = 24 * 60 // args.interval_minutes
        total_readings = args.nmis * args.days * intervals_per_day
        print(
            f"Generated {n_rows} rows ({size_mb:.1f} MiB) — "
            f"expected {total_readings:,} interval readings"
        )
        print()

        # Streaming count
        t = time.perf_counter()
        n = 0
        for _ in parse(path):
            n += 1
        e = time.perf_counter() - t
        print(
            f"  parse(path) -> for-loop count   {e*1000:>8.1f} ms  "
            f"({n/e/1e6:.2f} M readings/s, {size_mb/e:.1f} MiB/s)"
        )

        # Buffered facade
        with _timed("NEMReader().read_from_file") as _:
            r = NEMReader()
            r.read_from_file(str(path))

        # Columnar materialisation via row iterable (no pandas required)
        with _timed("to_columns(parse(path))") as _:
            cols = to_columns(parse(path))
        assert len(cols["NMI"]) == total_readings

        # Columnar fast path — parses straight into column lists, skipping
        # IntervalReading object allocation.
        with _timed("parse_to_columns(path) [fast path]") as _:
            cols2 = parse_to_columns(path)
        assert len(cols2["NMI"]) == total_readings

        # Pandas DataFrame via fast path
        try:
            import pandas as pd  # noqa: F401

            with _timed("to_dataframe(path) [fast path]") as _:
                from nem12_reader import to_dataframe

                df = to_dataframe(path)
            assert len(df) == total_readings
        except ImportError:
            print("  to_dataframe                     (pandas not installed; skipping)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
