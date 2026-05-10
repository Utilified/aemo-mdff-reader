"""nem12-reader — fast streaming reader for AEMO NEM12 / NEM13 files.

The recommended entry points for new code are:

>>> from nem12_reader import parse
>>> for reading in parse("metering.csv"):
...     ...

For convenience, :class:`NEMReader` provides a buffered facade and
``to_dataframe`` / ``to_csv`` helpers (the former requires pandas).
"""

from __future__ import annotations

from .parser import (
    NEM12ParseError,
    parse,
    parse_header,
    parse_to_columns,
    to_columns,
    to_dataframe,
    write_csv,
)
from .reader import INTERVAL_DATA_OUTPUT_HEADERS, NEMReader
from .types import Header, IntervalEvent, IntervalReading, NMIDetails

__version__ = "2.0.0"

__all__ = [
    "NEMReader",
    "Header",
    "IntervalEvent",
    "IntervalReading",
    "NMIDetails",
    "NEM12ParseError",
    "parse",
    "parse_header",
    "parse_to_columns",
    "to_columns",
    "to_dataframe",
    "write_csv",
    "INTERVAL_DATA_OUTPUT_HEADERS",
    "__version__",
]
