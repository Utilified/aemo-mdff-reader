"""Tests for the NEM13 (250 accumulation) interface."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from nem12_reader import (
    AccumulationReading,
    IntervalReading,
    parse_accumulations,
    parse_accumulations_to_columns,
    parse_all,
    to_accumulations_dataframe,
    write_accumulations_csv,
)

NEM13_FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem13.csv"
NEM12_FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem12.csv"


def test_parse_accumulations_count():
    accs = list(parse_accumulations(NEM13_FIXTURE))
    assert len(accs) == 3


def test_parse_accumulations_field_values():
    accs = list(parse_accumulations(NEM13_FIXTURE))
    a = accs[0]
    assert a.nmi == "NMI1234567"
    assert a.register_id == "E1"
    assert a.nmi_suffix == "E1"
    assert a.meter_serial_number == "METER000001"
    assert a.direction_indicator == "I"
    assert a.previous_register_read == pytest.approx(12345.0)
    assert a.previous_register_read_datetime == datetime(2023, 12, 1, 0, 0, 0)
    assert a.current_register_read == pytest.approx(12567.5)
    assert a.current_register_read_datetime == datetime(2024, 1, 1, 0, 0, 0)
    assert a.quantity == pytest.approx(222.5)
    assert a.uom == "KWH"
    assert a.next_scheduled_read_date == datetime(2024, 4, 1)
    assert a.previous_quality_method == "A"
    assert a.current_quality_method == "A"


def test_parse_accumulations_streaming_is_lazy():
    # parse_accumulations should accept a path AND a row iterable.
    rows = [
        ["100", "NEM13", "202401010000", "X", "Y"],
        [
            "250",
            "NMI",
            "C",
            "R",
            "S",
            "M",
            "MS",
            "I",
            "100.0",
            "20231201000000",
            "A",
            "",
            "",
            "200.0",
            "20240101000000",
            "A",
            "",
            "",
            "100.0",
            "KWH",
            "20240401",
            "20240102000000",
            "20240102010000",
        ],
        ["900"],
    ]
    out = list(parse_accumulations(rows))
    assert len(out) == 1
    assert out[0].quantity == pytest.approx(100.0)


def test_short_250_row_raises():
    rows = [
        ["100", "NEM13", "202401010000", "X", "Y"],
        ["250", "NMI", "C", "R"],
    ]
    from nem12_reader import NEM12ParseError

    with pytest.raises(NEM12ParseError):
        list(parse_accumulations(rows))


def test_parse_accumulations_to_columns_matches_iteration():
    cols = parse_accumulations_to_columns(NEM13_FIXTURE)
    assert len(cols["NMI"]) == 3
    nmis = list(cols["NMI"])
    assert nmis == ["NMI1234567", "NMI1234567", "NMI7654321"]
    assert all(len(v) == 3 for v in cols.values())


def test_parse_all_emits_both_record_types(tmp_path):
    # Build a hybrid file by concatenating the two fixtures, dropping the
    # extra header so the output is structurally valid.
    nem12 = NEM12_FIXTURE.read_text().splitlines()
    nem13 = NEM13_FIXTURE.read_text().splitlines()
    # Remove the second 100 header and the second 900 footer.
    combined = nem12[:-1] + [r for r in nem13 if not r.startswith("100")]
    out = []
    for r in parse_all(combined):
        out.append(r)
    intervals = [r for r in out if isinstance(r, IntervalReading)]
    accs = [r for r in out if isinstance(r, AccumulationReading)]
    # Three 300 rows × 48 intervals/day from the NEM12 fixture
    assert len(intervals) == 3 * 48
    assert len(accs) == 3


def test_to_accumulations_dataframe():
    pytest.importorskip("pandas")
    df = to_accumulations_dataframe(NEM13_FIXTURE)
    assert len(df) == 3
    assert {"NMI", "Quantity", "Register", "UOM"}.issubset(df.columns)
    assert df["Quantity"].iloc[0] == pytest.approx(222.5)


def test_write_accumulations_csv(tmp_path):
    out = tmp_path / "acc.csv"
    n = write_accumulations_csv(parse_accumulations(NEM13_FIXTURE), out)
    assert n == 3
    text = out.read_text()
    assert text.startswith("NMI,NMIConfiguration,")
    # Three data rows + header
    assert len(text.strip().splitlines()) == 4


def test_cli_accumulations_records(tmp_path):
    from nem12_reader.cli import main

    out = tmp_path / "out.csv"
    rc = main([str(NEM13_FIXTURE), "-o", str(out), "--records", "accumulations"])
    assert rc == 0
    text = out.read_text().splitlines()
    # header + 3 data rows
    assert len(text) == 4
    assert "NMI" in text[0]


def test_intervals_iterator_skips_250_rows():
    # The default `parse()` should ignore 250 records (NEM13).
    from nem12_reader import parse

    out = list(parse(NEM13_FIXTURE))
    assert out == []
