"""Generate a synthetic NEM12 file for tests / benchmarks.

Usage::

    python tests/fixtures/generate.py [out_path] [--nmis N] [--days D] [--interval-minutes M]

The output is deterministic for a given seed and contains no real NMIs
or meter serials.
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path
from typing import IO


def generate(
    out: IO[str],
    *,
    nmis: int = 4,
    days: int = 30,
    interval_minutes: int = 30,
    start_date: date = date(2024, 1, 1),
    seed: int = 0,
) -> int:
    rng = random.Random(seed)
    intervals_per_day = 24 * 60 // interval_minutes
    w = csv.writer(out)
    w.writerow(["100", "NEM12", "202401010000", "TESTGEN", "TESTGEN"])
    rows = 1
    for n in range(nmis):
        nmi = f"NMI{n:07d}"
        meter = f"METER{n:06d}"
        w.writerow(
            [
                "200",
                nmi,
                "E1Q1",
                "E1",
                "E1",
                "N1",
                meter,
                "KWH",
                str(interval_minutes),
                "",
            ]
        )
        rows += 1
        for d in range(days):
            day = start_date + timedelta(days=d)
            row = [
                "300",
                day.strftime("%Y%m%d"),
            ]
            row.extend(f"{rng.uniform(0, 5):.4f}" for _ in range(intervals_per_day))
            row.extend(["A", "", "", "", ""])
            w.writerow(row)
            rows += 1
    w.writerow(["900"])
    rows += 1
    return rows


def main() -> int:
    import sys

    p = argparse.ArgumentParser()
    p.add_argument("out", nargs="?", default="-")
    p.add_argument("--nmis", type=int, default=4)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--interval-minutes", type=int, default=30)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    if args.out == "-":
        rows = generate(
            sys.stdout,
            nmis=args.nmis,
            days=args.days,
            interval_minutes=args.interval_minutes,
            seed=args.seed,
        )
    else:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", newline="") as f:
            rows = generate(
                f,
                nmis=args.nmis,
                days=args.days,
                interval_minutes=args.interval_minutes,
                seed=args.seed,
            )
    # Print row count to stderr so the script's exit code is a clean
    # 0/non-zero (was previously the row count, which Python truncates
    # mod 256 inside SystemExit).
    print(f"wrote {rows} rows", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
