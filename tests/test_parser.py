"""Unit tests for the streaming NEM12 parser."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path

import pytest

from nem12_reader import (
    NEMReader,
    NEM12ParseError,
    parse,
    parse_header,
    parse_to_columns,
    to_columns,
    write_csv,
)


FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem12.csv"


def test_parse_header():
    h = parse_header(FIXTURE)
    assert h is not None
    assert h.version == "NEM12"
    assert h.from_participant == "RETAILER"
    assert h.datetime == datetime(2024, 1, 1, 0, 0, 0)


def test_parse_yields_correct_count():
    readings = list(parse(FIXTURE))
    # 3 × 300 records × 48 intervals/day (30-minute reads) = 144
    assert len(readings) == 3 * 48


def test_parse_first_reading_fields():
    r = next(iter(parse(FIXTURE)))
    assert r.nmi == "NMI1234567"
    assert r.meter_serial_number == "METER000001"
    assert r.register_id == "E1"
    assert r.uom == "KWH"
    assert r.interval_length == 30
    assert r.interval_index == 1
    assert r.interval_date == datetime(2024, 1, 1)
    assert r.interval_start == datetime(2024, 1, 1, 0, 0)
    assert r.interval_end == datetime(2024, 1, 1, 0, 30)
    assert r.value == pytest.approx(0.100)
    assert r.quality_method == "A"


def test_parse_interval_window_progresses():
    readings = list(parse(FIXTURE))
    # Within a single 300 row, intervals progress by IntervalLength.
    day1 = [r for r in readings if r.interval_date == datetime(2024, 1, 1) and r.register_id == "E1"]
    assert len(day1) == 48
    assert day1[0].interval_start == datetime(2024, 1, 1, 0, 0)
    assert day1[-1].interval_end == datetime(2024, 1, 2, 0, 0)


def test_parse_handles_second_register():
    readings = list(parse(FIXTURE))
    q1 = [r for r in readings if r.register_id == "Q1"]
    assert len(q1) == 48
    assert all(r.uom == "KVARH" for r in q1)


def test_parse_from_iterable_of_lines():
    lines = FIXTURE.read_text().splitlines()
    readings = list(parse(lines))
    assert len(readings) == 3 * 48


def test_parse_from_iterable_of_rows():
    with open(FIXTURE) as f:
        rows = list(csv.reader(f))
    readings = list(parse(rows))
    assert len(readings) == 3 * 48


def test_parse_from_file_object():
    with open(FIXTURE) as f:
        readings = list(parse(f))
    assert len(readings) == 3 * 48


def test_300_before_200_raises():
    rows = [["100", "NEM12", "202401010000", "X", "Y"], ["300", "20240101", "0.1"]]
    with pytest.raises(NEM12ParseError):
        list(parse(rows))


def test_short_300_row_raises():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "NMI", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "30", ""],
        ["300", "20240101", "0.1"],  # too few intervals
    ]
    with pytest.raises(NEM12ParseError):
        list(parse(rows))


def test_invalid_interval_length_raises():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "NMI", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "0", ""],
    ]
    with pytest.raises(NEM12ParseError):
        list(parse(rows))


def test_to_columns_returns_dict_of_lists():
    cols = to_columns(parse(FIXTURE))
    assert set(cols).issuperset({"NMI", "Value", "IntervalStart", "Interval"})
    n = len(cols["NMI"])
    assert n == 3 * 48
    assert all(len(v) == n for v in cols.values())


def test_parse_to_columns_matches_to_columns():
    a = to_columns(parse(FIXTURE))
    b = parse_to_columns(FIXTURE)
    assert a == b


def test_parse_to_columns_from_iterable():
    rows = list(csv.reader(open(FIXTURE)))
    a = parse_to_columns(FIXTURE)
    b = parse_to_columns(rows)
    assert a == b


def test_write_csv_roundtrip(tmp_path):
    out = tmp_path / "out.csv"
    n = write_csv(parse(FIXTURE), out)
    assert n == 3 * 48
    written = out.read_text().splitlines()
    # header + 144 rows
    assert len(written) == n + 1
    assert "NMI" in written[0]


def test_nem_reader_backward_compat():
    rdr = NEMReader()
    rdr.read_from_file(str(FIXTURE))
    assert len(rdr.readings) == 3 * 48
    assert rdr.filename == str(FIXTURE)


def test_pandas_dataframe_roundtrip():
    pd = pytest.importorskip("pandas")
    df = NEMReader.__new__(NEMReader)  # placeholder, use API directly
    rdr = NEMReader()
    rdr.read_from_file(str(FIXTURE))
    df = rdr.to_dataframe()
    assert len(df) == 3 * 48
    assert {"NMI", "Value", "IntervalStart"}.issubset(df.columns)


def test_streaming_does_not_materialise_when_unused(tmp_path):
    # Calling parse() should be lazy — verifying by passing a closed file
    # would actually fail eagerly because we open inside the generator.
    # Instead, generate a large source and confirm we can break early.
    rows = [["100", "NEM12", "202401010000", "X", "Y"]]
    rows.append(["200", "N", "E1Q1", "E1", "E1", "N1", "M", "KWH", "30", ""])
    for d in range(1, 6):
        rows.append(["300", f"2024010{d}"] + ["0.1"] * 48 + ["A", "", "", "", ""])
    rows.append(["900"])
    n = 0
    for _ in parse(rows):
        n += 1
        if n == 10:
            break
    assert n == 10
