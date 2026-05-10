"""Streaming NEM12 / NEM13 parser.

This module parses NEM12 and the structurally similar NEM13 files
defined by AEMO. It is a single-pass, allocation-light implementation
that yields :class:`IntervalReading` (300) and :class:`AccumulationReading`
(250) records without constructing an intermediate parse tree.

Spec target: AEMO Meter Data File Format Specification NEM12 & NEM13,
v2.6, effective 29 September 2024. Allowed-value enumerations are
exposed via :mod:`aemo_mdff_reader.spec`.
"""

from __future__ import annotations

import csv
import itertools
import os
import re
from datetime import datetime, timedelta
from typing import IO, Any, Dict, Iterable, Iterator, List, Optional, Sequence, Union

from .types import (
    AccumulationReading,
    B2BDetails,
    Header,
    IntervalEvent,
    IntervalReading,
    NMIDetails,
)

# Trailing timezone offset in ISO 8601 form: ``+HH:MM`` or ``+HHMM``.
# Anchored to the end of the string and requires at least 4 digits so we
# never accidentally match the dash inside an ISO date like ``2024-01-01``.
_TZ_OFFSET_RE = re.compile(r"([+-]\d{2}:\d{2}|[+-]\d{4})$")

HEADER_RECORD = "100"
NMI_RECORD = "200"
ACCUMULATION_RECORD = "250"
INTERVAL_RECORD = "300"
EVENT_RECORD = "400"
B2B_RECORD = "500"
ACCUMULATION_B2B_RECORD = "550"
END_RECORD = "900"

# Field counts per AEMO MDFF v2.6 (NEM12 / NEM13).
ACCUMULATION_FIELDS = 23  # 250 record

MINUTES_PER_DAY = 24 * 60

# Path-like is anything ``os.fspath`` can convert. Streams are anything
# yielding lines / iterable rows.
PathLike = Union[str, "os.PathLike[str]"]
RowSource = Union[PathLike, Iterable[Sequence[str]], Iterable[str], IO[str]]
Columns = Dict[str, List[Any]]


class NEM12ParseError(ValueError):
    """Raised when a NEM12 file violates the format in a way we cannot recover from."""


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse a NEM12 date/datetime field.

    Accepted forms (all return naive ``datetime`` objects — any timezone
    suffix on the input is silently stripped, matching the existing
    contract that callers attach the local AEMO market timezone
    themselves):

    * ``YYYYMMDD`` (spec: Date(8))
    * ``YYYYMMDDhhmmss`` (spec: DateTime(14))
    * ``YYYYMMDDhhmm`` (DateTime(12) — seen in some retailer exports)
    * ``YYYY-MM-DD`` (ISO 8601 date — tolerance for non-spec exports)
    * ``YYYY-MM-DDTHH:MM:SS`` and ``YYYY-MM-DD HH:MM:SS`` (ISO 8601
      date-time, with or without microseconds)
    * Any of the above followed by ``Z``, ``+HH:MM``, ``+HHMM``,
      ``-HH:MM``, or ``-HHMM`` — the timezone suffix is dropped.
    """
    if not value:
        return None

    # Strip trailing timezone suffix if present. The result is fed
    # straight back through the fixed-width or ISO branches below.
    if value.endswith("Z"):
        value = value[:-1]
    m = _TZ_OFFSET_RE.search(value)
    if m:
        value = value[: m.start()]

    n = len(value)
    if n == 14:
        return datetime(
            int(value[0:4]),
            int(value[4:6]),
            int(value[6:8]),
            int(value[8:10]),
            int(value[10:12]),
            int(value[12:14]),
        )
    if n == 12:  # YYYYMMDDhhmm — seen in some retailer exports
        return datetime(
            int(value[0:4]),
            int(value[4:6]),
            int(value[6:8]),
            int(value[8:10]),
            int(value[10:12]),
        )
    if n == 8:
        return datetime(int(value[0:4]), int(value[4:6]), int(value[6:8]))
    if n == 10 and value[4] == "-" and value[7] == "-":
        return datetime(int(value[0:4]), int(value[5:7]), int(value[8:10]))

    # ISO 8601 date-time fall-through, e.g. ``2024-01-01T00:00:00`` or
    # ``2024-01-01 00:00:00`` (with optional microseconds). datetime's
    # native ``fromisoformat`` is strict about the leading dashes /
    # colons; the basic form ``YYYYMMDDTHHMMSS`` is only recognised on
    # Python 3.11+, so we don't promise it.
    if "T" in value or " " in value:
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            pass
        else:
            return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt

    raise NEM12ParseError(f"Unrecognised date/time value: {value!r}")


def _parse_int(value: str) -> Optional[int]:
    if value == "" or value is None:
        return None
    return int(value)


def _parse_float(value: str) -> float:
    """Parse a numeric NEM12 cell.

    NEM12 uses decimal numbers without thousands separators. Empty cells
    (sometimes seen for missing intervals) are coerced to ``0.0`` so a
    single missing cell doesn't fail an entire row. Use the row's
    ``QualityMethod`` flag to distinguish a real zero from a missing
    reading — see :class:`IntervalReading` for the surfaced fields.
    """
    if value == "" or value is None:
        return 0.0
    return float(value)


class _ParserState:
    """Mutable state held across rows during a single parse."""

    __slots__ = ("current_nmi", "header", "interval_delta", "intervals_per_day")

    def __init__(self) -> None:
        self.header: Optional[Header] = None
        self.current_nmi: Optional[NMIDetails] = None
        self.intervals_per_day: int = 0
        self.interval_delta: Optional[timedelta] = None


_BOM = "﻿"


def _strip_bom(row: Sequence[str]) -> Sequence[str]:
    """Strip a UTF-8 BOM from the first cell of the first row, if present.

    Some retailer NEM12/NEM13 exports begin with a UTF-8 BOM. When read
    via plain UTF-8 the BOM survives into ``row[0]``, turning the record
    indicator ``"100"`` into ``"﻿100"`` and silently breaking parsing.
    """
    if row and isinstance(row[0], str) and row[0].startswith(_BOM):
        # Sequence may be tuple or list; rebuild as list to keep mutability semantics.
        first = row[0].lstrip(_BOM)
        return [first, *row[1:]]
    return row


def _open_rows(source: RowSource) -> Iterator[Sequence[str]]:
    """Yield rows from a path, file-like, or already-iterable row source.

    For paths, the file is opened with the ``utf-8-sig`` encoding so a
    leading UTF-8 BOM is consumed transparently. For file-like and
    iterable sources, a BOM on the first row's first cell is stripped
    explicitly.
    """
    # Path-like — handle BOM via utf-8-sig.
    if isinstance(source, (str, os.PathLike)):
        # newline='' is required for csv per the docs.
        with open(os.fspath(source), encoding="utf-8-sig", newline="") as f:
            yield from csv.reader(f)
        return

    # File-like (has .read but is not already an iterator of rows).
    if hasattr(source, "read") and not hasattr(source, "__next__"):
        first = True
        for row in csv.reader(source):  # type: ignore[arg-type]
            yield _strip_bom(row) if first else row
            first = False
        return

    # Iterable: peek at the first element to decide if it's raw lines or rows.
    it: Iterator[Any] = iter(source)
    try:
        first = next(it)
    except StopIteration:
        return
    chained: Iterator[Any] = itertools.chain([first], it)
    if isinstance(first, str):
        seen_first = False
        for row in csv.reader(chained):
            if not seen_first:
                seen_first = True
                yield _strip_bom(row)
            else:
                yield row
    else:
        # Already-split rows. Strip BOM from first row's first cell.
        seen_first = False
        for row in chained:
            if not seen_first:
                seen_first = True
                yield _strip_bom(row)
            else:
                yield row


def parse(source: RowSource) -> Iterator[IntervalReading]:
    """Parse a NEM12 file and yield :class:`IntervalReading` objects.

    ``source`` accepts any of:

    * a filesystem path (``str`` or ``os.PathLike``);
    * an open text stream / file-like object;
    * an iterable of raw CSV lines (``Iterable[str]``);
    * an iterable of already-split rows (``Iterable[Sequence[str]]``,
      e.g. a ``list[list[str]]`` you've built from
      ``csv.reader(...).splitlines()``).

    The pre-split-rows form is convenient when the data is already in
    memory — say, decoded from a multipart upload — without forcing it
    back through ``csv.reader``::

        rows = list(csv.reader(StringIO(payload)))
        for r in parse(rows):
            ...

    Iteration is lazy: memory use is O(1) in file size when ``source``
    is a path or a stream. Pre-loaded sources keep whatever memory the
    caller already paid for them, but the parser itself adds no extra.
    """
    state = _ParserState()
    rows = iter(_open_rows(source))

    for row in rows:
        if not row:
            continue
        record = row[0]

        if record == INTERVAL_RECORD:
            yield from _emit_intervals(row, state)
        elif record == NMI_RECORD:
            state.current_nmi = _parse_nmi(row)
            il = state.current_nmi.interval_length
            if il <= 0 or MINUTES_PER_DAY % il != 0:
                raise NEM12ParseError(f"IntervalLength {il} does not divide a 24-hour day")
            state.intervals_per_day = MINUTES_PER_DAY // il
            state.interval_delta = timedelta(minutes=il)
        elif record == HEADER_RECORD:
            state.header = _parse_header(row)
        elif record == EVENT_RECORD or record == B2B_RECORD:
            # 400 quality / 500 B2B rows attach to the most recent 300
            # row. The default streaming reader skips them — call
            # ``parse_events`` or ``parse_b2b`` to surface them.
            continue
        elif record == END_RECORD:
            return
        # Unknown record indicators (250, 550, enem12 600/610/700, ...)
        # are ignored here. Use ``parse_accumulations`` for 250 records,
        # ``parse_b2b`` for 500/550, or ``parse_all`` for 300+250 mixed.


def parse_header(source: RowSource) -> Optional[Header]:
    """Return only the file header, then stop reading."""
    for row in _open_rows(source):
        if row and row[0] == HEADER_RECORD:
            return _parse_header(row)
    return None


def _parse_header(row: Sequence[str]) -> Header:
    # 100, VersionHeader, DateTime, FromParticipant, ToParticipant
    if len(row) < 3:
        raise NEM12ParseError("100 header row missing required fields")
    return Header(
        version=row[1] if len(row) > 1 else "",
        datetime=_parse_datetime(row[2]) if len(row) > 2 else None,
        from_participant=row[3] if len(row) > 3 else "",
        to_participant=row[4] if len(row) > 4 else "",
    )


def _parse_nmi(row: Sequence[str]) -> NMIDetails:
    # 200, NMI, NMIConfiguration, RegisterID, NMISuffix,
    # MDMDataStreamIdentifier, MeterSerialNumber, UOM, IntervalLength,
    # NextScheduledReadDate (per AEMO MDFF v2.6 §4.3).
    #
    # IntervalLength: the spec restricts this to 5, 15, or 30 minutes. We
    # accept any divisor of 1440 for tolerance with non-conforming files;
    # callers wanting strict validation can compare against
    # ``aemo_mdff_reader.spec.ALLOWED_INTERVAL_LENGTHS``.
    if len(row) < 9:
        raise NEM12ParseError("200 NMI row missing required fields")
    try:
        interval_length = int(row[8])
    except ValueError as exc:
        raise NEM12ParseError(f"200 NMI row has non-integer IntervalLength: {row[8]!r}") from exc
    if interval_length <= 0 or interval_length > MINUTES_PER_DAY:
        raise NEM12ParseError(
            f"200 NMI row has IntervalLength={interval_length}; must be in 1..{MINUTES_PER_DAY}"
        )
    return NMIDetails(
        nmi=row[1],
        nmi_configuration=row[2],
        register_id=row[3] if len(row) > 3 else "",
        nmi_suffix=row[4],
        mdm_data_stream_identifier=row[5] if len(row) > 5 else "",
        meter_serial_number=row[6] if len(row) > 6 else "",
        uom=row[7],
        interval_length=interval_length,
        next_scheduled_read_date=_parse_datetime(row[9]) if len(row) > 9 else None,
    )


def _emit_intervals(row: Sequence[str], state: _ParserState) -> Iterator[IntervalReading]:
    nmi = state.current_nmi
    if nmi is None:
        raise NEM12ParseError("300 interval row encountered before any 200 NMI row")
    n = state.intervals_per_day
    delta = state.interval_delta
    expected_min = 2 + n  # 300 + IntervalDate + n values, then trailers (optional)
    if len(row) < expected_min:
        raise NEM12ParseError(
            f"300 row has {len(row)} fields, expected at least {expected_min} "
            f"for IntervalLength={nmi.interval_length}"
        )

    interval_date = _parse_datetime(row[1])
    if interval_date is None:
        raise NEM12ParseError("300 row missing IntervalDate")

    # Trailers: QualityMethod, ReasonCode, ReasonDescription,
    # UpdateDateTime, MSATSLoadDateTime — all optional in practice.
    tail = row[2 + n :]
    quality_method = tail[0] if len(tail) > 0 else ""
    reason_code = _parse_int(tail[1]) if len(tail) > 1 else None
    reason_description = tail[2] if len(tail) > 2 else ""
    update_datetime = _parse_datetime(tail[3]) if len(tail) > 3 else None
    msats_load_datetime = _parse_datetime(tail[4]) if len(tail) > 4 else None

    # Pre-bind locals for inner loop speed.
    _Reading = IntervalReading
    _nmi = nmi.nmi
    _meter = nmi.meter_serial_number
    _reg = nmi.register_id
    _suffix = nmi.nmi_suffix
    _uom = nmi.uom
    _il = nmi.interval_length

    start = interval_date
    base = 2
    for i in range(n):
        end = start + delta  # type: ignore[operator]
        yield _Reading(
            nmi=_nmi,
            meter_serial_number=_meter,
            register_id=_reg,
            nmi_suffix=_suffix,
            uom=_uom,
            interval_length=_il,
            interval_date=interval_date,
            interval_start=start,
            interval_end=end,
            interval_index=i + 1,
            value=_parse_float(row[base + i]),
            quality_method=quality_method,
            reason_code=reason_code,
            reason_description=reason_description,
            update_datetime=update_datetime,
            msats_load_datetime=msats_load_datetime,
        )
        start = end


def parse_to_columns(source: RowSource) -> Columns:
    """Single-pass columnar parse — skips per-cell row object allocation.

    This is the fast path for building a pandas DataFrame or writing a
    flat CSV from a path. It is typically 2–4× faster than
    ``to_columns(parse(path))`` because each interval cell becomes a
    primitive append into pre-bound list locals, with no
    :class:`IntervalReading` object created.

    The returned dict has the same column layout as :func:`to_columns`.
    """
    cols: Columns = {
        "NMI": [],
        "MeterSerial": [],
        "Register": [],
        "Suffix": [],
        "UOM": [],
        "IntervalLength": [],
        "IntervalDate": [],
        "IntervalStart": [],
        "IntervalEnd": [],
        "Interval": [],
        "Value": [],
        "Quality": [],
        "ReasonCode": [],
        "ReasonDescription": [],
        "UpdateDatetime": [],
        "MSATSLoadDatetime": [],
    }
    a_nmi = cols["NMI"].append
    a_meter = cols["MeterSerial"].append
    a_reg = cols["Register"].append
    a_suf = cols["Suffix"].append
    a_uom = cols["UOM"].append
    a_il = cols["IntervalLength"].append
    a_idate = cols["IntervalDate"].append
    a_istart = cols["IntervalStart"].append
    a_iend = cols["IntervalEnd"].append
    a_idx = cols["Interval"].append
    a_val = cols["Value"].append
    a_q = cols["Quality"].append
    a_rc = cols["ReasonCode"].append
    a_rd = cols["ReasonDescription"].append
    a_ud = cols["UpdateDatetime"].append
    a_mlt = cols["MSATSLoadDatetime"].append

    state = _ParserState()
    nmi_obj: Optional[NMIDetails] = None
    n = 0
    delta = None  # type: Optional[timedelta]

    for row in _open_rows(source):
        if not row:
            continue
        rec = row[0]
        if rec == INTERVAL_RECORD:
            if nmi_obj is None:
                raise NEM12ParseError("300 interval row encountered before any 200 NMI row")
            expected_min = 2 + n
            if len(row) < expected_min:
                raise NEM12ParseError(
                    f"300 row has {len(row)} fields, expected at least {expected_min}"
                )
            interval_date = _parse_datetime(row[1])
            if interval_date is None:
                raise NEM12ParseError("300 row missing IntervalDate")
            tail = row[2 + n :]
            quality = tail[0] if len(tail) > 0 else ""
            reason_code = _parse_int(tail[1]) if len(tail) > 1 else None
            reason_desc = tail[2] if len(tail) > 2 else ""
            update_dt = _parse_datetime(tail[3]) if len(tail) > 3 else None
            msats_dt = _parse_datetime(tail[4]) if len(tail) > 4 else None

            _nmi_v = nmi_obj.nmi
            _meter_v = nmi_obj.meter_serial_number
            _reg_v = nmi_obj.register_id
            _suf_v = nmi_obj.nmi_suffix
            _uom_v = nmi_obj.uom
            _il_v = nmi_obj.interval_length
            start = interval_date
            base = 2
            for i in range(n):
                end = start + delta  # type: ignore[operator]
                a_nmi(_nmi_v)
                a_meter(_meter_v)
                a_reg(_reg_v)
                a_suf(_suf_v)
                a_uom(_uom_v)
                a_il(_il_v)
                a_idate(interval_date)
                a_istart(start)
                a_iend(end)
                a_idx(i + 1)
                cell = row[base + i]
                a_val(0.0 if cell == "" else float(cell))
                a_q(quality)
                a_rc(reason_code)
                a_rd(reason_desc)
                a_ud(update_dt)
                a_mlt(msats_dt)
                start = end
        elif rec == NMI_RECORD:
            nmi_obj = _parse_nmi(row)
            il = nmi_obj.interval_length
            if il <= 0 or MINUTES_PER_DAY % il != 0:
                raise NEM12ParseError(f"IntervalLength {il} does not divide a 24-hour day")
            n = MINUTES_PER_DAY // il
            delta = timedelta(minutes=il)
        elif rec == HEADER_RECORD:
            state.header = _parse_header(row)
        elif rec == END_RECORD:
            break
        # 400/500/other records are skipped here.
    return cols


def to_columns(readings: Iterable[IntervalReading]) -> Columns:
    """Materialise an iterable of readings into a dict of column lists.

    Use :func:`parse_to_columns` directly when you want to skip the
    per-cell :class:`IntervalReading` object allocation — it parses
    straight into columns in one pass.
    """
    cols: Columns = {
        "NMI": [],
        "MeterSerial": [],
        "Register": [],
        "Suffix": [],
        "UOM": [],
        "IntervalLength": [],
        "IntervalDate": [],
        "IntervalStart": [],
        "IntervalEnd": [],
        "Interval": [],
        "Value": [],
        "Quality": [],
        "ReasonCode": [],
        "ReasonDescription": [],
        "UpdateDatetime": [],
        "MSATSLoadDatetime": [],
    }
    # Pre-bind list.append to avoid attribute lookups in the hot loop.
    app_nmi = cols["NMI"].append
    app_meter = cols["MeterSerial"].append
    app_reg = cols["Register"].append
    app_suf = cols["Suffix"].append
    app_uom = cols["UOM"].append
    app_il = cols["IntervalLength"].append
    app_idate = cols["IntervalDate"].append
    app_istart = cols["IntervalStart"].append
    app_iend = cols["IntervalEnd"].append
    app_idx = cols["Interval"].append
    app_val = cols["Value"].append
    app_q = cols["Quality"].append
    app_rc = cols["ReasonCode"].append
    app_rd = cols["ReasonDescription"].append
    app_ud = cols["UpdateDatetime"].append
    app_md = cols["MSATSLoadDatetime"].append
    for r in readings:
        app_nmi(r.nmi)
        app_meter(r.meter_serial_number)
        app_reg(r.register_id)
        app_suf(r.nmi_suffix)
        app_uom(r.uom)
        app_il(r.interval_length)
        app_idate(r.interval_date)
        app_istart(r.interval_start)
        app_iend(r.interval_end)
        app_idx(r.interval_index)
        app_val(r.value)
        app_q(r.quality_method)
        app_rc(r.reason_code)
        app_rd(r.reason_description)
        app_ud(r.update_datetime)
        app_md(r.msats_load_datetime)
    return cols


def to_dataframe(source: Union[RowSource, Iterable[IntervalReading]]) -> Any:
    """Build a pandas DataFrame from a NEM12 source or reading iterable.

    Accepts a path, file-like, or an iterable of :class:`IntervalReading`
    objects. When given a path/file, takes the columnar fast-path for
    a 2–4× speedup over iterating through Python row objects.

    .. note::
       This materialises every reading. For files larger than a few
       hundred MiB use :func:`iter_dataframes` instead — it yields
       fixed-size DataFrame chunks and stays bounded in memory.

    Requires ``pandas`` (``pip install aemo-mdff-reader[pandas]``).
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "to_dataframe requires pandas. Install it with "
            "'pip install aemo-mdff-reader[pandas]' or 'pip install pandas'."
        ) from exc

    # Fast path: path-like or file-like — parse straight into columns.
    if isinstance(source, (str, os.PathLike)) or hasattr(source, "read"):
        return pd.DataFrame(parse_to_columns(source))  # type: ignore[arg-type]
    # Iterable of IntervalReading — use the row-by-row builder.
    return pd.DataFrame(to_columns(source))  # type: ignore[arg-type]


def iter_dataframes(
    source: Union[RowSource, Iterable[IntervalReading]],
    chunk_size: int = 100_000,
) -> Iterator[Any]:
    """Yield pandas DataFrames in chunks of ``chunk_size`` interval readings.

    Memory cost is O(chunk_size), independent of the source file size
    — letting a single workflow process arbitrarily large NEM12 files
    without OOM. ``chunk_size`` defaults to 100,000 readings, which is
    roughly 30–60 MiB of DataFrame depending on string fields.

    >>> import pandas as pd
    >>> from aemo_mdff_reader import iter_dataframes
    >>> for df in iter_dataframes("huge.csv", chunk_size=50_000):
    ...     df.groupby("NMI")["Value"].sum().to_csv("partial.csv", mode="a")

    For columnar processing without pandas, see
    :func:`iter_columns_chunks`.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "iter_dataframes requires pandas. Install it with "
            "'pip install aemo-mdff-reader[pandas]' or 'pip install pandas'."
        ) from exc

    # Always go through the row-by-row generator so the function
    # accepts both a source (path/file/iterable of rows) and an
    # iterable of pre-built IntervalReading objects.
    if isinstance(source, (str, os.PathLike)) or hasattr(source, "read"):
        readings: Iterable[IntervalReading] = parse(source)  # type: ignore[arg-type]
    else:
        readings = source  # type: ignore[assignment]

    from .aggregate import iter_chunks  # local import to avoid cycle

    for batch in iter_chunks(readings, chunk_size):
        yield pd.DataFrame(to_columns(batch))


def iter_columns_chunks(
    source: Union[RowSource, Iterable[IntervalReading]],
    chunk_size: int = 100_000,
) -> Iterator[Columns]:
    """Yield :data:`Columns` dicts in chunks of ``chunk_size`` rows.

    Pandas-free counterpart to :func:`iter_dataframes`. Memory bound to
    O(chunk_size). Useful for chunked parquet writes via pyarrow, or
    feeding a database in batches with the ``executemany`` API.
    """
    if isinstance(source, (str, os.PathLike)) or hasattr(source, "read"):
        readings: Iterable[IntervalReading] = parse(source)  # type: ignore[arg-type]
    else:
        readings = source  # type: ignore[assignment]

    from .aggregate import iter_chunks  # local import to avoid cycle

    for batch in iter_chunks(readings, chunk_size):
        yield to_columns(batch)


def write_csv(readings: Iterable[IntervalReading], output: Union[PathLike, IO[str]]) -> int:
    """Write readings as a flat CSV. Returns the number of rows written.

    Pure-stdlib path that does not require pandas.
    """
    columns = [
        "NMI",
        "MeterSerial",
        "Register",
        "Suffix",
        "UOM",
        "IntervalLength",
        "IntervalDate",
        "IntervalStart",
        "IntervalEnd",
        "Interval",
        "Value",
        "Quality",
        "ReasonCode",
        "ReasonDescription",
        "UpdateDatetime",
        "MSATSLoadDatetime",
    ]
    if isinstance(output, (str, os.PathLike)):
        # Force UTF-8 — without an explicit encoding Python falls back to
        # the platform default (cp1252 on Windows) which may misencode
        # any non-ASCII characters carried over from the source file.
        f = open(os.fspath(output), "w", encoding="utf-8", newline="")
        close = True
    else:
        f = output  # type: ignore[assignment]
        close = False
    try:
        w = csv.writer(f)
        w.writerow(columns)
        count = 0
        for r in readings:
            w.writerow(
                [
                    r.nmi,
                    r.meter_serial_number,
                    r.register_id,
                    r.nmi_suffix,
                    r.uom,
                    r.interval_length,
                    r.interval_date.strftime("%Y-%m-%d") if r.interval_date else "",
                    r.interval_start.isoformat() if r.interval_start else "",
                    r.interval_end.isoformat() if r.interval_end else "",
                    r.interval_index,
                    r.value,
                    r.quality_method,
                    "" if r.reason_code is None else r.reason_code,
                    r.reason_description,
                    r.update_datetime.isoformat() if r.update_datetime else "",
                    r.msats_load_datetime.isoformat() if r.msats_load_datetime else "",
                ]
            )
            count += 1
        return count
    finally:
        if close:
            f.close()


# --------------------------------------------------------------------------
# NEM13 — 250 accumulation records
# --------------------------------------------------------------------------


def _parse_accumulation(row: Sequence[str]) -> AccumulationReading:
    """Parse a single 250 (NEM13) accumulation row.

    Field order follows AEMO MDFF v2.6 §5.3 (NEM13):

      1. RecordIndicator (250)
      2. NMI                              13. PreviousReasonDescription
      3. NMIConfiguration                 14. CurrentRegisterRead
      4. RegisterID                       15. CurrentRegisterReadDateTime
      5. NMISuffix                        16. CurrentQualityMethod
      6. MDMDataStreamIdentifier          17. CurrentReasonCode
      7. MeterSerialNumber                18. CurrentReasonDescription
      8. DirectionIndicator               19. Quantity
      9. PreviousRegisterRead             20. UOM
     10. PreviousRegisterReadDateTime     21. NextScheduledReadDate
     11. PreviousQualityMethod            22. UpdateDateTime
     12. PreviousReasonCode               23. MSATSLoadDateTime
    """
    if len(row) < 20:
        raise NEM12ParseError(
            f"250 accumulation row has {len(row)} fields; spec requires at least 20"
        )

    def _get(i: int) -> str:
        return row[i] if i < len(row) else ""

    return AccumulationReading(
        nmi=row[1],
        nmi_configuration=row[2],
        register_id=row[3],
        nmi_suffix=row[4],
        mdm_data_stream_identifier=_get(5),
        meter_serial_number=row[6],
        direction_indicator=_get(7),
        previous_register_read=_parse_float(row[8]),
        previous_register_read_datetime=_parse_datetime(_get(9)),
        previous_quality_method=_get(10),
        previous_reason_code=_parse_int(_get(11)),
        previous_reason_description=_get(12),
        current_register_read=_parse_float(row[13]),
        current_register_read_datetime=_parse_datetime(_get(14)),
        current_quality_method=_get(15),
        current_reason_code=_parse_int(_get(16)),
        current_reason_description=_get(17),
        quantity=_parse_float(row[18]),
        uom=row[19],
        next_scheduled_read_date=_parse_datetime(_get(20)),
        update_datetime=_parse_datetime(_get(21)),
        msats_load_datetime=_parse_datetime(_get(22)),
    )


def parse_accumulations(source: RowSource) -> Iterator[AccumulationReading]:
    """Yield NEM13 250 (accumulation / manual-read) records as a stream.

    NEM13 250 records are self-contained — unlike NEM12 300 records they
    do not depend on a parent 200 row. Iteration is lazy; memory is O(1).
    """
    for row in _open_rows(source):
        if not row:
            continue
        rec = row[0]
        if rec == ACCUMULATION_RECORD:
            yield _parse_accumulation(row)
        elif rec == END_RECORD:
            return


def parse_all(
    source: RowSource,
) -> Iterator[Union[IntervalReading, AccumulationReading]]:
    """Yield NEM12 300 interval readings and NEM13 250 accumulation
    records together, in file order.

    Use this for files that interleave 300 and 250 rows. Other record
    types are not surfaced — call :func:`parse_events` for 400 quality
    flags or :func:`parse_b2b` for 500 / 550 transactions.
    """
    state = _ParserState()
    nmi_obj: Optional[NMIDetails] = None
    n = 0
    delta: Optional[timedelta] = None

    for row in _open_rows(source):
        if not row:
            continue
        rec = row[0]
        if rec == INTERVAL_RECORD:
            if nmi_obj is None:
                raise NEM12ParseError("300 interval row encountered before any 200 NMI row")
            yield from _emit_intervals_with(row, nmi_obj, n, delta)
        elif rec == ACCUMULATION_RECORD:
            yield _parse_accumulation(row)
        elif rec == NMI_RECORD:
            nmi_obj = _parse_nmi(row)
            il = nmi_obj.interval_length
            if il <= 0 or MINUTES_PER_DAY % il != 0:
                raise NEM12ParseError(f"IntervalLength {il} does not divide a 24-hour day")
            n = MINUTES_PER_DAY // il
            delta = timedelta(minutes=il)
        elif rec == HEADER_RECORD:
            state.header = _parse_header(row)
        elif rec == END_RECORD:
            return


def _emit_intervals_with(
    row: Sequence[str],
    nmi_obj: NMIDetails,
    n: int,
    delta: Optional[timedelta],
) -> Iterator[IntervalReading]:
    """Variant of :func:`_emit_intervals` that takes its NMI context as args.

    Used by :func:`parse_all` so it doesn't need a shared mutable state object.
    """
    state = _ParserState()
    state.current_nmi = nmi_obj
    state.intervals_per_day = n
    state.interval_delta = delta
    yield from _emit_intervals(row, state)


# --------------------------------------------------------------------------
# Columnar helpers for accumulations
# --------------------------------------------------------------------------


def parse_accumulations_to_columns(source: RowSource) -> Columns:
    """Single-pass columnar parse of NEM13 250 records."""
    cols: Columns = {
        "NMI": [],
        "NMIConfiguration": [],
        "Register": [],
        "Suffix": [],
        "MDMDataStreamIdentifier": [],
        "MeterSerial": [],
        "DirectionIndicator": [],
        "PreviousRegisterRead": [],
        "PreviousRegisterReadDatetime": [],
        "PreviousQualityMethod": [],
        "PreviousReasonCode": [],
        "PreviousReasonDescription": [],
        "CurrentRegisterRead": [],
        "CurrentRegisterReadDatetime": [],
        "CurrentQualityMethod": [],
        "CurrentReasonCode": [],
        "CurrentReasonDescription": [],
        "Quantity": [],
        "UOM": [],
        "NextScheduledReadDate": [],
        "UpdateDatetime": [],
        "MSATSLoadDatetime": [],
    }
    for r in parse_accumulations(source):
        cols["NMI"].append(r.nmi)
        cols["NMIConfiguration"].append(r.nmi_configuration)
        cols["Register"].append(r.register_id)
        cols["Suffix"].append(r.nmi_suffix)
        cols["MDMDataStreamIdentifier"].append(r.mdm_data_stream_identifier)
        cols["MeterSerial"].append(r.meter_serial_number)
        cols["DirectionIndicator"].append(r.direction_indicator)
        cols["PreviousRegisterRead"].append(r.previous_register_read)
        cols["PreviousRegisterReadDatetime"].append(r.previous_register_read_datetime)
        cols["PreviousQualityMethod"].append(r.previous_quality_method)
        cols["PreviousReasonCode"].append(r.previous_reason_code)
        cols["PreviousReasonDescription"].append(r.previous_reason_description)
        cols["CurrentRegisterRead"].append(r.current_register_read)
        cols["CurrentRegisterReadDatetime"].append(r.current_register_read_datetime)
        cols["CurrentQualityMethod"].append(r.current_quality_method)
        cols["CurrentReasonCode"].append(r.current_reason_code)
        cols["CurrentReasonDescription"].append(r.current_reason_description)
        cols["Quantity"].append(r.quantity)
        cols["UOM"].append(r.uom)
        cols["NextScheduledReadDate"].append(r.next_scheduled_read_date)
        cols["UpdateDatetime"].append(r.update_datetime)
        cols["MSATSLoadDatetime"].append(r.msats_load_datetime)
    return cols


def to_accumulations_dataframe(source: RowSource) -> Any:
    """Build a pandas DataFrame of NEM13 250 records.

    Requires ``pandas`` (``pip install aemo-mdff-reader[pandas]``).
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "to_accumulations_dataframe requires pandas. Install it with "
            "'pip install aemo-mdff-reader[pandas]' or 'pip install pandas'."
        ) from exc
    return pd.DataFrame(parse_accumulations_to_columns(source))


def write_accumulations_csv(
    accumulations: Iterable[AccumulationReading], output: Union[PathLike, IO[str]]
) -> int:
    """Write NEM13 250 records as a flat CSV. Returns the row count."""
    columns = [
        "NMI",
        "NMIConfiguration",
        "Register",
        "Suffix",
        "MDMDataStreamIdentifier",
        "MeterSerial",
        "DirectionIndicator",
        "PreviousRegisterRead",
        "PreviousRegisterReadDatetime",
        "PreviousQualityMethod",
        "PreviousReasonCode",
        "PreviousReasonDescription",
        "CurrentRegisterRead",
        "CurrentRegisterReadDatetime",
        "CurrentQualityMethod",
        "CurrentReasonCode",
        "CurrentReasonDescription",
        "Quantity",
        "UOM",
        "NextScheduledReadDate",
        "UpdateDatetime",
        "MSATSLoadDatetime",
    ]
    if isinstance(output, (str, os.PathLike)):
        f = open(os.fspath(output), "w", encoding="utf-8", newline="")
        close = True
    else:
        f = output  # type: ignore[assignment]
        close = False
    try:
        w = csv.writer(f)
        w.writerow(columns)
        count = 0
        for r in accumulations:
            w.writerow(
                [
                    r.nmi,
                    r.nmi_configuration,
                    r.register_id,
                    r.nmi_suffix,
                    r.mdm_data_stream_identifier,
                    r.meter_serial_number,
                    r.direction_indicator,
                    r.previous_register_read,
                    r.previous_register_read_datetime.isoformat()
                    if r.previous_register_read_datetime
                    else "",
                    r.previous_quality_method,
                    "" if r.previous_reason_code is None else r.previous_reason_code,
                    r.previous_reason_description,
                    r.current_register_read,
                    r.current_register_read_datetime.isoformat()
                    if r.current_register_read_datetime
                    else "",
                    r.current_quality_method,
                    "" if r.current_reason_code is None else r.current_reason_code,
                    r.current_reason_description,
                    r.quantity,
                    r.uom,
                    r.next_scheduled_read_date.isoformat() if r.next_scheduled_read_date else "",
                    r.update_datetime.isoformat() if r.update_datetime else "",
                    r.msats_load_datetime.isoformat() if r.msats_load_datetime else "",
                ]
            )
            count += 1
        return count
    finally:
        if close:
            f.close()


# --------------------------------------------------------------------------
# 400 Interval events / 500 + 550 B2B records
# --------------------------------------------------------------------------


def _parse_interval_event(
    row: Sequence[str],
    nmi: NMIDetails,
    interval_date: datetime,
) -> IntervalEvent:
    """Parse a single 400 (Interval Event) row.

    Field order per AEMO MDFF v2.6 §4.5:
        1. RecordIndicator (400)
        2. StartInterval                4. QualityMethod
        3. EndInterval                  5. ReasonCode
                                        6. ReasonDescription
    """
    if len(row) < 4:
        raise NEM12ParseError(f"400 event row has {len(row)} fields; spec requires at least 4")

    def _get(i: int) -> str:
        return row[i] if i < len(row) else ""

    return IntervalEvent(
        nmi=nmi.nmi,
        meter_serial_number=nmi.meter_serial_number,
        register_id=nmi.register_id,
        interval_date=interval_date,
        start_interval=int(row[1]),
        end_interval=int(row[2]),
        quality_method=_get(3),
        reason_code=_parse_int(_get(4)),
        reason_description=_get(5),
    )


def _parse_b2b(row: Sequence[str]) -> B2BDetails:
    """Parse a 500 or 550 B2B detail row.

    500 fields: 500, TransCode, RetServiceOrder, ReadDateTime, IndexRead.
    550 fields: 550, PreviousTransCode, PreviousRetServiceOrder,
                CurrentTransCode, CurrentRetServiceOrder.
    """
    rec = row[0]

    def _get(i: int) -> str:
        return row[i] if i < len(row) else ""

    if rec == B2B_RECORD:  # 500
        return B2BDetails(
            record_kind=rec,
            trans_code=_get(1),
            ret_service_order=_get(2),
            read_datetime=_parse_datetime(_get(3)),
            index_read=_get(4),
        )
    if rec == ACCUMULATION_B2B_RECORD:  # 550
        return B2BDetails(
            record_kind=rec,
            previous_trans_code=_get(1),
            previous_ret_service_order=_get(2),
            current_trans_code=_get(3),
            current_ret_service_order=_get(4),
        )
    raise NEM12ParseError(f"Unsupported B2B record indicator: {rec!r}")


def parse_events(source: RowSource) -> Iterator[IntervalEvent]:
    """Yield NEM12 400 (interval event) rows attached to their parent
    200 / 300 context.

    Iteration is lazy and O(1) memory.
    """
    state = _ParserState()
    last_interval_date: Optional[datetime] = None
    for row in _open_rows(source):
        if not row:
            continue
        rec = row[0]
        if rec == NMI_RECORD:
            state.current_nmi = _parse_nmi(row)
        elif rec == INTERVAL_RECORD:
            if state.current_nmi is None:
                raise NEM12ParseError("300 interval row encountered before any 200 NMI row")
            last_interval_date = _parse_datetime(row[1])
        elif rec == EVENT_RECORD:
            if state.current_nmi is None or last_interval_date is None:
                raise NEM12ParseError("400 event row encountered without a parent 300 row")
            yield _parse_interval_event(row, state.current_nmi, last_interval_date)
        elif rec == END_RECORD:
            return


def parse_b2b(source: RowSource) -> Iterator[B2BDetails]:
    """Yield 500 (NEM12 B2B) and 550 (NEM13 B2B) records as a stream."""
    for row in _open_rows(source):
        if not row:
            continue
        rec = row[0]
        if rec in (B2B_RECORD, ACCUMULATION_B2B_RECORD):
            yield _parse_b2b(row)
        elif rec == END_RECORD:
            return


# --------------------------------------------------------------------------
# Validation utilities
# --------------------------------------------------------------------------


def nmi_checksum(nmi: str) -> int:
    """Compute the AEMO NMI checksum digit (0-9).

    Implements the AEMO NMI Checksum Algorithm: for the 10-character NMI,
    each character is converted to its ASCII value; characters at *odd*
    positions counting from the right (starting at 1) are doubled; the
    decimal digits of all values are summed; the checksum is
    ``(10 - (sum % 10)) % 10``.

    Iterating left-to-right (``i = 0..9``), position-from-the-right is
    ``10 - i``, which is odd exactly when ``i`` is even — so we double
    when ``i % 2 == 0`` (left-to-right indices 0, 2, 4, 6, 8).

    Raises :class:`ValueError` if ``nmi`` is not exactly 10 characters
    or contains a non-printable / non-ASCII character.
    """
    if len(nmi) != 10:
        raise ValueError(f"NMI must be exactly 10 characters, got {nmi!r}")
    if any(not (32 < ord(c) < 127) for c in nmi):
        raise ValueError(f"NMI contains non-printable characters: {nmi!r}")
    total = 0
    for i, ch in enumerate(nmi):
        v = ord(ch)
        if i % 2 == 0:  # odd position from the right
            v *= 2
        while v:
            total += v % 10
            v //= 10
    return (10 - (total % 10)) % 10


def validate_nmi(nmi: str, checksum_digit: Optional[str] = None) -> bool:
    """Return True if the NMI is structurally valid.

    A NEM12/13 NMI is exactly 10 printable ASCII characters. If
    ``checksum_digit`` is provided, it is also compared against the
    computed AEMO NMI checksum.
    """
    try:
        computed = nmi_checksum(nmi)
    except ValueError:
        return False
    if checksum_digit is None:
        return True
    return str(computed) == checksum_digit


def validate_file(source: RowSource) -> List[str]:
    """Run lightweight structural checks against a NEM12 / NEM13 file.

    Returns a list of human-readable problem descriptions; an empty list
    means the file passed all structural checks. This does not replace
    full parsing — it surfaces common issues early (missing 100 header,
    missing 900 footer, 300 row outside any 200 context, wrong 250 field
    count, NMI structural validity) so callers can fail fast.

    .. note::
       ``source`` is consumed once. Pass a path or a fresh file handle if
       you intend to also call :func:`parse` afterward — passing a
       generator or single-pass iterator will leave it exhausted.
    """
    issues: List[str] = []
    saw_header = False
    saw_footer = False
    current_nmi: Optional[NMIDetails] = None
    seen_nmis: set[str] = set()
    line_no = 0
    for row in _open_rows(source):
        line_no += 1
        if not row:
            continue
        rec = row[0]
        if rec == HEADER_RECORD:
            if saw_header:
                issues.append(f"line {line_no}: duplicate 100 header")
            saw_header = True
            if line_no != 1:
                issues.append(f"line {line_no}: 100 header should be the first row")
            try:
                _parse_header(row)
            except NEM12ParseError as exc:
                issues.append(f"line {line_no}: {exc}")
        elif rec == NMI_RECORD:
            try:
                current_nmi = _parse_nmi(row)
                if not validate_nmi(current_nmi.nmi):
                    issues.append(f"line {line_no}: NMI {current_nmi.nmi!r} has invalid structure")
                seen_nmis.add(current_nmi.nmi)
            except NEM12ParseError as exc:
                issues.append(f"line {line_no}: {exc}")
        elif rec == INTERVAL_RECORD:
            if current_nmi is None:
                issues.append(f"line {line_no}: 300 row encountered before any 200 NMI row")
        elif rec == ACCUMULATION_RECORD:
            if len(row) < 20:
                issues.append(
                    f"line {line_no}: 250 row has {len(row)} fields, spec requires at least 20"
                )
        elif rec == END_RECORD:
            saw_footer = True
    if not saw_header:
        issues.append("missing 100 header record")
    if not saw_footer:
        issues.append("missing 900 footer record")
    return issues


__all__ = [
    "ACCUMULATION_FIELDS",
    "NEM12ParseError",
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
    "to_accumulations_dataframe",
    "to_columns",
    "to_dataframe",
    "validate_file",
    "validate_nmi",
    "write_accumulations_csv",
    "write_csv",
]
