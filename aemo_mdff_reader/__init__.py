"""aemo-mdff-reader — fast streaming reader for AEMO NEM12 / NEM13 files.

Recommended entry points:

>>> from aemo_mdff_reader import parse                  # NEM12 300 records
>>> from aemo_mdff_reader import parse_accumulations    # NEM13 250 records
>>> from aemo_mdff_reader import parse_all              # both, in file order

Each iterator is lazy (O(1) memory). For pandas DataFrames, see
:func:`to_dataframe` (NEM12) and :func:`to_accumulations_dataframe` (NEM13).

Spec compatibility: AEMO MDFF v2.6 (effective 29 September 2024). The
allowed-value tables — quality flags, transaction codes, reason codes,
units of measure — are exposed as constants in :mod:`aemo_mdff_reader.spec`.
"""

from __future__ import annotations

from . import aggregate, spec
from .parser import (
    NEM12ParseError,
    iter_columns_chunks,
    iter_dataframes,
    nmi_checksum,
    parse,
    parse_accumulations,
    parse_accumulations_to_columns,
    parse_all,
    parse_b2b,
    parse_events,
    parse_header,
    parse_to_columns,
    to_accumulations_dataframe,
    to_columns,
    to_dataframe,
    validate_file,
    validate_nmi,
    write_accumulations_csv,
    write_csv,
)
from .reader import INTERVAL_DATA_OUTPUT_HEADERS, NEMReader
from .types import (
    AccumulationReading,
    B2BDetails,
    Header,
    IntervalEvent,
    IntervalReading,
    NMIDetails,
)

__version__ = "2.0.0"

__all__ = [
    "INTERVAL_DATA_OUTPUT_HEADERS",
    "AccumulationReading",
    "B2BDetails",
    "Header",
    "IntervalEvent",
    "IntervalReading",
    "NEM12ParseError",
    "NEMReader",
    "NMIDetails",
    "__version__",
    "aggregate",
    "iter_columns_chunks",
    "iter_dataframes",
    "nmi_checksum",
    "parse",
    "parse_accumulations",
    "parse_accumulations_to_columns",
    "parse_all",
    "parse_b2b",
    "parse_events",
    "parse_header",
    "parse_to_columns",
    "spec",
    "to_accumulations_dataframe",
    "to_columns",
    "to_dataframe",
    "validate_file",
    "validate_nmi",
    "write_accumulations_csv",
    "write_csv",
]
