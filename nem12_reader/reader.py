"""Backward-compatible NEMReader facade.

The original :class:`NEMReader` class built an in-memory tree of records
and walked it twice (once to build, once to flatten). The new
implementation streams through :mod:`nem12_reader.parser` and only
materialises results when the user asks for them — typically to a
DataFrame or CSV.

The legacy method names are preserved so existing code continues to
work; new code should prefer :func:`nem12_reader.parser.parse` directly.
"""

from __future__ import annotations

from typing import Any, Iterable, Iterator, List, Optional, Sequence

from .parser import Columns, parse, to_columns, to_dataframe, write_csv
from .types import IntervalReading

# Kept for backward compatibility with the old INTERVAL_DATA_OUTPUT_HEADERS export.
INTERVAL_DATA_OUTPUT_HEADERS = [
    "NMI",
    "MeterSerial",
    "Register",
    "Date",
    "Interval",
    "IntervalLength",
    "UOM",
    "IntervalValue",
    "Quality",
    "UpdateDatetime",
]


class NEMReader:
    """Reads NEM12 / NEM13 files using the AEMO MDFF specification (v2.6).

    See :mod:`nem12_reader.spec` for the spec version, effective date,
    and the allowed-value enumerations referenced in the spec.
    """

    INTERVAL_DATA_OUTPUT_HEADERS = INTERVAL_DATA_OUTPUT_HEADERS

    def __init__(self) -> None:
        self._readings: Optional[List[IntervalReading]] = None
        self._source_filename: Optional[str] = None

    @property
    def filename(self) -> Optional[str]:
        return self._source_filename

    @property
    def readings(self) -> List[IntervalReading]:
        if self._readings is None:
            raise RuntimeError("Call read_from_file() or read_from_array() first.")
        return self._readings

    def read_from_array(self, array: Iterable[Sequence[str]]) -> None:
        """Reads from an iterable of pre-split rows."""
        self._readings = list(parse(array))

    def read_from_file(self, filename: str) -> None:
        """Read a NEM12 CSV file from disk and buffer every interval.

        Memory note: this materialises the full reading list, so peak
        usage scales with the file. For files larger than a few hundred
        MiB use :func:`nem12_reader.parse` (streaming, O(1) memory) or
        :func:`nem12_reader.iter_dataframes` (bounded, O(chunk_size))
        instead.
        """
        self._source_filename = filename
        self._readings = list(parse(filename))

    def __iter__(self) -> Iterator[IntervalReading]:
        """Iterate over the buffered readings.

        Lets callers write ``for r in reader: ...`` after
        :meth:`read_from_file` or :meth:`read_from_array` instead of
        going through ``reader.readings``.
        """
        return iter(self.readings)

    def __len__(self) -> int:
        """Number of buffered readings (after ``read_from_file``)."""
        return len(self.readings)

    def to_dataframe(self) -> Any:
        """Materialise readings into a pandas DataFrame.

        Requires the ``pandas`` extra. When the buffered file path is
        known, this re-parses via the columnar fast path for a 2–4×
        speedup over iterating the in-memory readings list.
        """
        if self._source_filename is not None:
            return to_dataframe(self._source_filename)
        return to_dataframe(self.readings)

    def to_csv(self, filename: str) -> int:
        """Write readings as a flat CSV file. Returns the row count."""
        return write_csv(self.readings, filename)

    def to_columns(self) -> Columns:
        """Return readings as a dict of column lists (no pandas required)."""
        return to_columns(self.readings)


__all__ = ["INTERVAL_DATA_OUTPUT_HEADERS", "NEMReader"]
