"""Streaming NEM12 parser.

This module parses NEM12 (and the structurally similar NEM13) files
defined in the AEMO MDFF specification. It is a single-pass, allocation-
light implementation that yields :class:`IntervalReading` objects without
constructing an intermediate parse tree.

Reference: AEMO Meter Data File Format (MDFF) v1.02 — NEM12/NEM13.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import IO, Iterable, Iterator, List, Optional, Sequence, Union

import csv
import itertools
import os

from .types import Header, IntervalEvent, IntervalReading, NMIDetails


HEADER_RECORD = "100"
NMI_RECORD = "200"
INTERVAL_RECORD = "300"
EVENT_RECORD = "400"
B2B_RECORD = "500"
END_RECORD = "900"

MINUTES_PER_DAY = 24 * 60

# Path-like is anything ``os.fspath`` can convert. Streams are anything
# yielding lines / iterable rows.
PathLike = Union[str, "os.PathLike[str]"]
RowSource = Union[PathLike, Iterable[Sequence[str]], IO]


class NEM12ParseError(ValueError):
    """Raised when a NEM12 file violates the format in a way we cannot recover from."""


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse a NEM12 date/datetime field.

    The spec allows YYYYMMDD (8) and YYYYMMDDhhmmss (14). We also accept
    ISO date (10) for tolerance with some retailer exports.
    """
    if not value:
        return None
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
    raise NEM12ParseError(f"Unrecognised date/time value: {value!r}")


def _parse_int(value: str) -> Optional[int]:
    if value == "" or value is None:
        return None
    return int(value)


def _parse_float(value: str) -> float:
    # NEM12 uses decimal numbers without thousands separators. Empty string
    # is occasionally seen for missing intervals; we treat as 0.0 rather
    # than failing the whole row.
    if value == "" or value is None:
        return 0.0
    return float(value)


class _ParserState:
    """Mutable state held across rows during a single parse."""

    __slots__ = ("header", "current_nmi", "intervals_per_day", "interval_delta")

    def __init__(self) -> None:
        self.header: Optional[Header] = None
        self.current_nmi: Optional[NMIDetails] = None
        self.intervals_per_day: int = 0
        self.interval_delta: Optional[timedelta] = None


def _open_rows(source: RowSource) -> Iterator[Sequence[str]]:
    """Yield rows from a path, file-like, or already-iterable row source."""
    # Path-like
    if isinstance(source, (str, os.PathLike)):
        # newline='' is required for csv per the docs.
        with open(os.fspath(source), "r", newline="") as f:
            yield from csv.reader(f)
        return
    # File-like (has .read but is not already an iterator of rows)
    if hasattr(source, "read") and not hasattr(source, "__next__"):
        yield from csv.reader(source)  # type: ignore[arg-type]
        return
    # Iterable: peek at the first element to decide if it's raw lines or rows
    it = iter(source)  # type: ignore[arg-type]
    try:
        first = next(it)
    except StopIteration:
        return
    chained = itertools.chain([first], it)
    if isinstance(first, str):
        yield from csv.reader(chained)  # type: ignore[arg-type]
    else:
        yield from chained  # type: ignore[misc]


def parse(source: RowSource) -> Iterator[IntervalReading]:
    """Parse a NEM12 file and yield :class:`IntervalReading` objects.

    ``source`` may be a path, an open file/text stream, or an iterable
    yielding either raw CSV lines (str) or already-split rows (list/tuple
    of str). Iteration is lazy: memory use is O(1) in file size.
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
                raise NEM12ParseError(
                    f"IntervalLength {il} does not divide a 24-hour day"
                )
            state.intervals_per_day = MINUTES_PER_DAY // il
            state.interval_delta = timedelta(minutes=il)
        elif record == HEADER_RECORD:
            state.header = _parse_header(row)
        elif record == EVENT_RECORD or record == B2B_RECORD:
            # Quality/B2B detail rows attach to the most recent 300 row.
            # We don't currently surface them through the streaming reader;
            # see ``parse_with_events`` for that.
            continue
        elif record == END_RECORD:
            return
        # Unknown record indicators (e.g. enem12 600/610/700, nem13 250/550)
        # are ignored by the default streaming reader. Use ``parse_records``
        # for a less filtered view.


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
    # NextScheduledReadDate
    if len(row) < 9:
        raise NEM12ParseError("200 NMI row missing required fields")
    return NMIDetails(
        nmi=row[1],
        nmi_configuration=row[2],
        register_id=row[3] if len(row) > 3 else "",
        nmi_suffix=row[4],
        mdm_data_stream_identifier=row[5] if len(row) > 5 else "",
        meter_serial_number=row[6] if len(row) > 6 else "",
        uom=row[7],
        interval_length=int(row[8]),
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


def parse_to_columns(source: RowSource) -> dict:
    """Single-pass columnar parse — skips per-cell row object allocation.

    This is the fast path for building a pandas DataFrame or writing a
    flat CSV from a path. It is typically 2–4× faster than
    ``to_columns(parse(path))`` because each interval cell becomes a
    primitive append into pre-bound list locals, with no
    :class:`IntervalReading` object created.

    The returned dict has the same column layout as :func:`to_columns`.
    """
    cols = {
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
                raise NEM12ParseError(
                    f"IntervalLength {il} does not divide a 24-hour day"
                )
            n = MINUTES_PER_DAY // il
            delta = timedelta(minutes=il)
        elif rec == HEADER_RECORD:
            state.header = _parse_header(row)
        elif rec == END_RECORD:
            break
        # 400/500/other records are skipped here.
    return cols


def to_columns(readings: Iterable[IntervalReading]) -> dict:
    """Materialise an iterable of readings into a dict of column lists.

    Use :func:`parse_to_columns` directly when you want to skip the
    per-cell :class:`IntervalReading` object allocation — it parses
    straight into columns in one pass.
    """
    cols = {
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
    a = cols["NMI"].append
    b = cols["MeterSerial"].append
    c = cols["Register"].append
    d = cols["Suffix"].append
    e = cols["UOM"].append
    f = cols["IntervalLength"].append
    g = cols["IntervalDate"].append
    h = cols["IntervalStart"].append
    i = cols["IntervalEnd"].append
    j = cols["Interval"].append
    k = cols["Value"].append
    l = cols["Quality"].append
    m = cols["ReasonCode"].append
    n = cols["ReasonDescription"].append
    o = cols["UpdateDatetime"].append
    p = cols["MSATSLoadDatetime"].append
    for r in readings:
        a(r.nmi)
        b(r.meter_serial_number)
        c(r.register_id)
        d(r.nmi_suffix)
        e(r.uom)
        f(r.interval_length)
        g(r.interval_date)
        h(r.interval_start)
        i(r.interval_end)
        j(r.interval_index)
        k(r.value)
        l(r.quality_method)
        m(r.reason_code)
        n(r.reason_description)
        o(r.update_datetime)
        p(r.msats_load_datetime)
    return cols


def to_dataframe(source):
    """Build a pandas DataFrame from a NEM12 source or reading iterable.

    Accepts a path, file-like, or an iterable of :class:`IntervalReading`
    objects. When given a path/file, takes the columnar fast-path for
    a 2–4× speedup over iterating through Python row objects.

    Requires ``pandas`` (``pip install nem12-reader[pandas]``).
    """
    try:
        import pandas as pd  # noqa: WPS433 — optional dep
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "to_dataframe requires pandas. Install it with "
            "'pip install nem12-reader[pandas]' or 'pip install pandas'."
        ) from exc

    # Fast path: path-like or file-like — parse straight into columns.
    if isinstance(source, (str, os.PathLike)) or hasattr(source, "read"):
        return pd.DataFrame(parse_to_columns(source))
    # Iterable of IntervalReading — use the row-by-row builder.
    return pd.DataFrame(to_columns(source))


def write_csv(readings: Iterable[IntervalReading], output: Union[PathLike, IO]) -> int:
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
        f = open(os.fspath(output), "w", newline="")
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


__all__ = [
    "parse",
    "parse_header",
    "to_columns",
    "to_dataframe",
    "write_csv",
    "NEM12ParseError",
]
