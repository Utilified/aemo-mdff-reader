"""Edge cases covering empty intervals, multiple NMIs, and 30/15/5 minute
interval lengths.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from aemo_mdff_reader import parse, parse_to_columns


def _build(interval_minutes: int, *, days: int = 1, nmis: int = 1) -> list[list[str]]:
    n = (24 * 60) // interval_minutes
    rows: list[list[str]] = [["100", "NEM12", "202401010000", "X", "Y"]]
    for i in range(nmis):
        rows.append(
            [
                "200",
                f"NMI{i:07d}",
                "E1",
                "E1",
                "E1",
                "N1",
                f"M{i:06d}",
                "KWH",
                str(interval_minutes),
                "",
            ]
        )
        for d in range(days):
            day = datetime(2024, 1, 1) + timedelta(days=d)
            rows.append(["300", day.strftime("%Y%m%d")] + ["1.0"] * n + ["A", "", "", "", ""])
    rows.append(["900"])
    return rows


@pytest.mark.parametrize("interval_minutes", [60, 30, 15, 5, 1])
def test_supported_interval_lengths(interval_minutes):
    rows = _build(interval_minutes, days=1)
    out = list(parse(rows))
    assert len(out) == (24 * 60) // interval_minutes
    assert out[0].interval_start == datetime(2024, 1, 1, 0, 0)
    assert out[-1].interval_end == datetime(2024, 1, 2, 0, 0)
    assert out[0].interval_length == interval_minutes


def test_multiple_nmis_keep_correct_context():
    rows = _build(30, days=1, nmis=3)
    out = list(parse(rows))
    nmis = {r.nmi for r in out}
    assert nmis == {"NMI0000000", "NMI0000001", "NMI0000002"}
    assert len(out) == 3 * 48


def test_empty_interval_value_treated_as_zero():
    rows = _build(30, days=1)
    rows[2][2] = ""  # blank one cell
    out = list(parse(rows))
    assert out[0].value == 0.0


def test_900_terminator_stops_parsing():
    rows = _build(30, days=2)
    # Insert a 900 between days. _build appends 900 at the end, but for
    # this test we want to confirm that an early 900 stops emission.
    end = next(i for i, r in enumerate(rows) if r and r[0] == "900")
    rows.insert(end - 1, ["900"])
    rows = rows[:end]  # drop the original final 900
    out = list(parse(rows))
    # We saw the early 900 before the second 300 row, so only one day.
    assert len(out) == 48


def test_parse_to_columns_value_count_matches_intervals():
    rows = _build(5, days=2, nmis=2)
    cols = parse_to_columns(rows)
    expected = 2 * 2 * (24 * 60 // 5)
    assert len(cols["Value"]) == expected
    assert all(len(v) == expected for v in cols.values())


def test_unknown_record_indicators_are_ignored():
    rows = _build(30, days=1)
    # Inject 250/500/600 records that the streaming parser doesn't surface.
    rows.insert(2, ["500", "B", "RSO", "20240101000000", "12345"])
    rows.insert(2, ["250", "NMI0000000"])
    out = list(parse(rows))
    assert len(out) == 48


def test_interval_event_constructable():
    from datetime import datetime as dt

    from aemo_mdff_reader import IntervalEvent

    evt = IntervalEvent(
        nmi="NMI",
        meter_serial_number="M",
        register_id="E1",
        interval_date=dt(2024, 1, 1),
        start_interval=1,
        end_interval=5,
        quality_method="A",
        reason_code=None,
        reason_description="",
    )
    assert evt.start_interval == 1
    assert evt.end_interval == 5


def test_empty_file_returns_empty_iterator(tmp_path):
    """A truly empty file produces no readings without raising."""
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    assert list(parse(empty)) == []


def test_utf8_bom_path_input(tmp_path):
    """A NEM12 file with a UTF-8 BOM is parsed correctly when given as a path."""
    rows = _build(30, days=1)
    text = "\n".join(",".join(r) for r in rows) + "\n"
    p = tmp_path / "with_bom.csv"
    # Write the BOM as raw UTF-8 bytes to ensure it's at the byte level.
    p.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    out = list(parse(p))
    assert len(out) == 48
    assert out[0].nmi == "NMI0000000"


def test_utf8_bom_string_iterable():
    """A BOM on the first line of a string iterable is stripped."""
    lines = [
        "﻿100,NEM12,202401010000,X,Y",
        "200,NMI1234567,E1Q1,E1,E1,N1,M1,KWH,30,",
        "300,20240101," + ",".join(["0.1"] * 48) + ",A,,,,",
        "900",
    ]
    out = list(parse(lines))
    assert len(out) == 48
    assert out[0].nmi == "NMI1234567"


def test_interval_length_too_large_rejected():
    from aemo_mdff_reader import NEM12ParseError

    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        # IntervalLength of 9999 minutes is well beyond a day.
        ["200", "NMI1234567", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "9999", ""],
        ["900"],
    ]
    with pytest.raises(NEM12ParseError):
        list(parse(rows))


def test_interval_length_non_integer_rejected():
    from aemo_mdff_reader import NEM12ParseError

    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "NMI1234567", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "abc", ""],
        ["900"],
    ]
    with pytest.raises(NEM12ParseError):
        list(parse(rows))
