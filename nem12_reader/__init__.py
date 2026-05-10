"""nem12-reader — fast streaming reader for AEMO NEM12 / NEM13 files.

Recommended entry points:

>>> from nem12_reader import parse                  # NEM12 300 records
>>> from nem12_reader import parse_accumulations    # NEM13 250 records
>>> from nem12_reader import parse_all              # both, in file order

Each iterator is lazy (O(1) memory). For pandas DataFrames, see
:func:`to_dataframe` (NEM12) and :func:`to_accumulations_dataframe` (NEM13).
"""

from __future__ import annotations

from .parser import (
    NEM12ParseError,
    parse,
    parse_accumulations,
    parse_accumulations_to_columns,
    parse_all,
    parse_header,
    parse_to_columns,
    to_accumulations_dataframe,
    to_columns,
    to_dataframe,
    write_accumulations_csv,
    write_csv,
)
from .reader import INTERVAL_DATA_OUTPUT_HEADERS, NEMReader
from .types import (
    AccumulationReading,
    Header,
    IntervalEvent,
    IntervalReading,
    NMIDetails,
)

__version__ = "2.0.0"

__all__ = [
    "INTERVAL_DATA_OUTPUT_HEADERS",
    "AccumulationReading",
    "Header",
    "IntervalEvent",
    "IntervalReading",
    "NEM12ParseError",
    "NEMReader",
    "NMIDetails",
    "__version__",
    "parse",
    "parse_accumulations",
    "parse_accumulations_to_columns",
    "parse_all",
    "parse_header",
    "parse_to_columns",
    "to_accumulations_dataframe",
    "to_columns",
    "to_dataframe",
    "write_accumulations_csv",
    "write_csv",
]
