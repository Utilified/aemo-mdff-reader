"""Roll a NEM12 file up into daily totals per channel.

Streams in O(1) memory: works on multi-GB files. Output is CSV on
stdout, suitable for piping into other tools.

Usage:  python examples/02_daily_totals.py path/to/file.csv > daily.csv
"""

from __future__ import annotations

import csv
import sys

from nem12_reader import parse
from nem12_reader.aggregate import daily_totals


def main(path: str) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(
        ["NMI", "Register", "Suffix", "UOM", "Date", "Total", "IntervalCount", "QualityFlags"]
    )
    for d in daily_totals(parse(path)):
        writer.writerow(
            [
                d.nmi,
                d.register_id,
                d.nmi_suffix,
                d.uom,
                d.interval_date.strftime("%Y-%m-%d"),
                f"{d.total:.4f}",
                d.interval_count,
                "|".join(sorted(d.unique_quality_flags)),
            ]
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    main(sys.argv[1])
