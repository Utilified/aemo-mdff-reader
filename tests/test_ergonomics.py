"""Tests for v2-ergonomic helpers: to_dict(), QMM properties,
aggregate helpers, NEMReader iteration, and CLI filter flags.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from nem12_reader import (
    AccumulationReading,
    B2BDetails,
    Header,
    IntervalEvent,
    IntervalReading,
    NEMReader,
    NMIDetails,
    aggregate,
    parse,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem12.csv"
NEM13_FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem13.csv"


# ---------------------------------------------------------------------------
# to_dict()
# ---------------------------------------------------------------------------


def test_interval_reading_to_dict_round_trips():
    r = next(iter(parse(FIXTURE)))
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["nmi"] == r.nmi
    assert d["value"] == r.value
    assert d["interval_start"] == r.interval_start
    # Must contain every slot.
    assert set(d) == set(IntervalReading.__slots__)


def test_accumulation_reading_to_dict():
    from nem12_reader import parse_accumulations

    r = next(iter(parse_accumulations(NEM13_FIXTURE)))
    d = r.to_dict()
    assert d["nmi"] == r.nmi
    assert d["quantity"] == r.quantity
    assert set(d) == set(AccumulationReading.__slots__)


def test_header_to_dict():
    from nem12_reader import parse_header

    h = parse_header(FIXTURE)
    assert h is not None
    d = h.to_dict()
    assert d["version"] == "NEM12"
    assert set(d) == set(Header.__slots__)


def test_nmi_details_to_dict():
    nmi = NMIDetails(
        nmi="NMI1234567",
        nmi_configuration="E1Q1",
        register_id="E1",
        nmi_suffix="E1",
        mdm_data_stream_identifier="N1",
        meter_serial_number="M1",
        uom="KWH",
        interval_length=30,
        next_scheduled_read_date=None,
    )
    d = nmi.to_dict()
    assert d["interval_length"] == 30
    assert set(d) == set(NMIDetails.__slots__)


def test_interval_event_to_dict():
    e = IntervalEvent(
        nmi="N",
        meter_serial_number="M",
        register_id="E1",
        interval_date=datetime(2024, 1, 1),
        start_interval=1,
        end_interval=5,
        quality_method="S52",
        reason_code=24,
        reason_description="",
    )
    d = e.to_dict()
    assert d["start_interval"] == 1
    assert set(d) == set(IntervalEvent.__slots__)


def test_b2b_to_dict():
    b = B2BDetails(record_kind="500", trans_code="N")
    d = b.to_dict()
    assert d["record_kind"] == "500"
    assert d["trans_code"] == "N"
    assert d["previous_trans_code"] is None
    assert set(d) == set(B2BDetails.__slots__)


# ---------------------------------------------------------------------------
# QMM split — quality_flag / method_flag
# ---------------------------------------------------------------------------


def _make_reading(quality_method: str) -> IntervalReading:
    return IntervalReading(
        nmi="N",
        meter_serial_number="M",
        register_id="E1",
        nmi_suffix="E1",
        uom="KWH",
        interval_length=30,
        interval_date=datetime(2024, 1, 1),
        interval_start=datetime(2024, 1, 1, 0, 0),
        interval_end=datetime(2024, 1, 1, 0, 30),
        interval_index=1,
        value=1.0,
        quality_method=quality_method,
        reason_code=None,
        reason_description="",
        update_datetime=None,
        msats_load_datetime=None,
    )


@pytest.mark.parametrize(
    "qm,expected_q,expected_m",
    [
        ("A", "A", ""),
        ("V", "V", ""),
        ("S52", "S", "52"),
        ("F17", "F", "17"),
        ("E03", "E", "03"),
        ("", "", ""),
    ],
)
def test_interval_reading_qmm_split(qm, expected_q, expected_m):
    r = _make_reading(qm)
    assert r.quality_flag == expected_q
    assert r.method_flag == expected_m


def test_interval_event_qmm_split():
    e = IntervalEvent(
        nmi="N",
        meter_serial_number="M",
        register_id="E1",
        interval_date=datetime(2024, 1, 1),
        start_interval=1,
        end_interval=5,
        quality_method="S52",
        reason_code=24,
        reason_description="",
    )
    assert e.quality_flag == "S"
    assert e.method_flag == "52"


def test_accumulation_qmm_split():
    a = AccumulationReading(
        nmi="N",
        nmi_configuration="E1",
        register_id="E1",
        nmi_suffix="E1",
        mdm_data_stream_identifier="N1",
        meter_serial_number="M",
        direction_indicator="I",
        previous_register_read=100.0,
        previous_register_read_datetime=datetime(2024, 1, 1),
        previous_quality_method="A",
        previous_reason_code=None,
        previous_reason_description="",
        current_register_read=200.0,
        current_register_read_datetime=datetime(2024, 2, 1),
        current_quality_method="S77",
        current_reason_code=24,
        current_reason_description="",
        quantity=100.0,
        uom="KWH",
        next_scheduled_read_date=None,
        update_datetime=None,
        msats_load_datetime=None,
    )
    assert a.previous_quality_flag == "A"
    assert a.previous_method_flag == ""
    assert a.current_quality_flag == "S"
    assert a.current_method_flag == "77"


# ---------------------------------------------------------------------------
# aggregate.group_by_nmi / daily_totals
# ---------------------------------------------------------------------------


def test_group_by_nmi_yields_one_group_per_channel():
    groups = [(key, list(g)) for key, g in aggregate.group_by_nmi(parse(FIXTURE))]
    # The fixture has three 200 records sharing NMI but on different
    # registers (E1 / Q1) and one extra register repeating; verify the
    # composite key separates them.
    keys = [k for k, _ in groups]
    assert all(isinstance(k, aggregate.ChannelKey) for k in keys)
    assert len({k for k in keys}) == len(keys), "no duplicate channel keys expected"


def test_daily_totals_sums_intervals_per_day():
    totals = list(aggregate.daily_totals(parse(FIXTURE)))
    # The 30-min fixture has 3 × 300 rows × 48 intervals/day. We get
    # one DailyTotal per (channel, day).
    assert len(totals) == 3
    for t in totals:
        assert t.interval_count == 48
        assert isinstance(t, aggregate.DailyTotal)
        assert t.total > 0
        assert t.unique_quality_flags == frozenset({"A"})


def test_daily_totals_streaming_with_gaps_in_quality():
    # Forge a single-day stream with mixed quality flags and confirm
    # the unique_quality_flags set captures both.
    base = _make_reading("A")
    sub = _make_reading("S52")
    sub.value = 2.0
    sub.interval_index = 2
    sub.interval_start = datetime(2024, 1, 1, 0, 30)
    sub.interval_end = datetime(2024, 1, 1, 1, 0)
    out = list(aggregate.daily_totals([base, sub]))
    assert len(out) == 1
    assert out[0].total == pytest.approx(3.0)
    assert out[0].unique_quality_flags == frozenset({"A", "S"})


def test_daily_totals_handles_empty_input():
    assert list(aggregate.daily_totals([])) == []


# ---------------------------------------------------------------------------
# NEMReader iteration
# ---------------------------------------------------------------------------


def test_nem_reader_is_iterable():
    rdr = NEMReader()
    rdr.read_from_file(str(FIXTURE))
    n = sum(1 for _ in rdr)
    assert n == 3 * 48


def test_nem_reader_len():
    rdr = NEMReader()
    rdr.read_from_file(str(FIXTURE))
    assert len(rdr) == 3 * 48


def test_nem_reader_iter_before_load_raises():
    rdr = NEMReader()
    with pytest.raises(RuntimeError):
        iter(rdr)


# ---------------------------------------------------------------------------
# CLI --nmi / --start / --end
# ---------------------------------------------------------------------------


def test_cli_nmi_filter_keeps_only_matching(tmp_path, capsys):
    from nem12_reader.cli import main

    out = tmp_path / "out.csv"
    rc = main([str(FIXTURE), "-o", str(out), "--nmi", "NMI1234567"])
    assert rc == 0
    text = out.read_text()
    # 3 × 48 readings + 1 header line = 145
    assert len(text.splitlines()) == 1 + 3 * 48
    for line in text.splitlines()[1:]:
        assert line.startswith("NMI1234567,")


def test_cli_nmi_filter_drops_non_matching(tmp_path):
    from nem12_reader.cli import main

    out = tmp_path / "out.csv"
    rc = main([str(FIXTURE), "-o", str(out), "--nmi", "DOES_NOT_EXIST"])
    assert rc == 0
    # Just the header — no data rows.
    assert out.read_text().count("\n") == 1


def test_cli_start_end_dates(tmp_path):
    from nem12_reader.cli import main

    out = tmp_path / "out.csv"
    # The fixture covers 2024-01-01 and 2024-01-02. Restrict to day 2.
    rc = main([str(FIXTURE), "-o", str(out), "--start", "2024-01-02"])
    assert rc == 0
    rows = out.read_text().splitlines()[1:]
    # Day 2 only: NMI1234567 has E1 (48 rows) on 20240102; Q1 register
    # has only day 1, so it's filtered out.
    assert len(rows) == 48
    assert all("2024-01-02" in r for r in rows)


def test_cli_invalid_date_argument():
    from nem12_reader.cli import main

    with pytest.raises(SystemExit):
        main([str(FIXTURE), "--start", "not-a-date"])
