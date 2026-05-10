"""Tests for 400 Interval Event and 500 / 550 B2B record parsing."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from nem12_reader import (
    B2BDetails,
    IntervalEvent,
    NEM12ParseError,
    parse_b2b,
    parse_events,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem12.csv"


def test_parse_events_yields_interval_events():
    events = list(parse_events(FIXTURE))
    # The fixture contains a single 400 row attached to the second 300 row.
    assert len(events) == 1
    e = events[0]
    assert isinstance(e, IntervalEvent)
    assert e.nmi == "NMI1234567"
    assert e.start_interval == 1
    assert e.end_interval == 5
    assert e.quality_method == "S"
    assert e.reason_code == 1
    assert e.reason_description == "Substituted opening intervals"
    # The 400 row sits under the day-2 300 record.
    assert e.interval_date == datetime(2024, 1, 2)


def test_parse_events_short_400_row_raises():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "NMI1234567", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "30", ""],
        ["300", "20240101"] + ["0.1"] * 48 + ["A", "", "", "", ""],
        ["400", "1"],
    ]
    with pytest.raises(NEM12ParseError):
        list(parse_events(rows))


def test_parse_events_400_before_300_raises():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "NMI1234567", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "30", ""],
        ["400", "1", "5", "S", "1", "Foo"],
    ]
    with pytest.raises(NEM12ParseError):
        list(parse_events(rows))


def test_parse_b2b_500_record():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["500", "S", "RSO12345", "20240101000000", "12345.6"],
        ["900"],
    ]
    out = list(parse_b2b(rows))
    assert len(out) == 1
    b = out[0]
    assert isinstance(b, B2BDetails)
    assert b.record_kind == "500"
    assert b.trans_code == "S"
    assert b.ret_service_order == "RSO12345"
    assert b.read_datetime == datetime(2024, 1, 1, 0, 0, 0)
    assert b.index_read == "12345.6"


def test_parse_b2b_550_record():
    rows = [
        ["100", "NEM13", "202401010000", "X", "Y"],
        ["550", "S", "RSO_PREV", "T", "RSO_CURR"],
        ["900"],
    ]
    out = list(parse_b2b(rows))
    assert len(out) == 1
    b = out[0]
    assert b.record_kind == "550"
    assert b.previous_trans_code == "S"
    assert b.previous_ret_service_order == "RSO_PREV"
    assert b.current_trans_code == "T"
    assert b.current_ret_service_order == "RSO_CURR"


def test_parse_b2b_skips_unrelated_records():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "NMI1234567", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "30", ""],
        ["300", "20240101"] + ["0.1"] * 48 + ["A", "", "", "", ""],
        ["500", "T", "RSO", "20240101000000", ""],
        ["900"],
    ]
    out = list(parse_b2b(rows))
    assert len(out) == 1
    assert out[0].trans_code == "T"
