"""Filter a NEM12 file by NMI / date range and load the result into pandas.

Requires the `pandas` extra:  pip install nem12-reader[pandas]

Usage:  python examples/03_filter_to_dataframe.py path/to/file.csv NMI1234567
"""

from __future__ import annotations

import sys
from datetime import date

import pandas as pd  # noqa: F401  — fails fast if not installed

from nem12_reader import parse, to_dataframe


def main(path: str, nmi: str) -> None:
    # Fast path: build a DataFrame, then filter in pandas.
    df = to_dataframe(path)
    df = df[df["NMI"] == nmi]
    print(f"Wide DataFrame: {len(df)} rows for {nmi!r}")
    print(df.head())
    print()

    # Streaming alternative: filter while iterating, materialise only
    # what we keep. Better when the file is huge and we want a small
    # slice.
    target_day = date(2024, 1, 1)
    matching = [
        r.to_dict() for r in parse(path) if r.nmi == nmi and r.interval_date.date() == target_day
    ]
    print(f"Streaming subset: {len(matching)} readings on {target_day}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)
    main(sys.argv[1], sys.argv[2])
