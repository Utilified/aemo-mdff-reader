"""Load a NEM12 file and print summary information about its contents.

Usage:  python examples/01_load_and_inspect.py path/to/file.csv
"""

from __future__ import annotations

import sys
from collections import Counter

from nem12_reader import parse, parse_header


def main(path: str) -> None:
    header = parse_header(path)
    if header is None:
        print(f"{path}: no 100 header — invalid NEM12 file")
        return

    print(f"File:        {path}")
    print(f"Version:     {header.version}")
    print(f"Created:     {header.datetime}")
    print(f"From → To:   {header.from_participant} → {header.to_participant}")
    print()

    # Walk the readings once and count NMIs / quality flags / interval span.
    nmi_intervals: Counter = Counter()
    flag_breakdown: Counter = Counter()
    earliest = None
    latest = None
    for r in parse(path):
        nmi_intervals[(r.nmi, r.register_id, r.nmi_suffix, r.uom)] += 1
        flag_breakdown[r.quality_flag] += 1
        if earliest is None or r.interval_start < earliest:
            earliest = r.interval_start
        if latest is None or r.interval_end > latest:
            latest = r.interval_end

    print(f"Date range:  {earliest}  →  {latest}")
    print(f"Quality:     {dict(flag_breakdown)}")
    print()
    print("Per-channel interval counts:")
    for (nmi, reg, suffix, uom), count in sorted(nmi_intervals.items()):
        print(f"  {nmi:<12}  {reg:<6} {suffix:<3} {uom:<6} {count} intervals")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    main(sys.argv[1])
