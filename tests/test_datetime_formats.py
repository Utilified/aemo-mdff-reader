"""Datetime parser format coverage."""

from __future__ import annotations

from datetime import datetime

import pytest

from aemo_mdff_reader.parser import NEM12ParseError, _parse_datetime


@pytest.mark.parametrize(
    "value,expected",
    [
        # Empty
        ("", None),
        # Spec fixed-width forms
        ("20240101", datetime(2024, 1, 1)),
        ("20240101000000", datetime(2024, 1, 1, 0, 0, 0)),
        ("20240131123456", datetime(2024, 1, 31, 12, 34, 56)),
        ("202401312359", datetime(2024, 1, 31, 23, 59)),  # YYYYMMDDhhmm
        # ISO date (non-spec but tolerated)
        ("2024-02-29", datetime(2024, 2, 29)),  # leap year
        # ISO date-time, T- and space-separated
        ("2024-01-01T00:00:00", datetime(2024, 1, 1, 0, 0, 0)),
        ("2024-01-01 12:34:56", datetime(2024, 1, 1, 12, 34, 56)),
        ("2024-01-01T12:34:56.789", datetime(2024, 1, 1, 12, 34, 56, 789000)),
        # Trailing timezone suffix is silently stripped, returning naive.
        ("2024-01-01T00:00:00Z", datetime(2024, 1, 1, 0, 0, 0)),
        ("2024-01-01T00:00:00+10:00", datetime(2024, 1, 1, 0, 0, 0)),
        ("2024-01-01T00:00:00+1000", datetime(2024, 1, 1, 0, 0, 0)),
        ("2024-01-01T00:00:00-05:00", datetime(2024, 1, 1, 0, 0, 0)),
        # Tz suffix on a date-only field (real-world non-spec retailer output).
        ("20240120+1000", datetime(2024, 1, 20)),
        ("2024-01-20+10:00", datetime(2024, 1, 20)),
        # Tz suffix on a 14-char fixed-width datetime.
        ("20240131123456+1000", datetime(2024, 1, 31, 12, 34, 56)),
    ],
)
def test_parse_datetime_supported_formats(value, expected):
    got = _parse_datetime(value)
    assert got == expected
    if got is not None:
        # Contract: every parsed datetime is naive. Callers attach the
        # market timezone (typically Australia/Brisbane) themselves.
        assert got.tzinfo is None


@pytest.mark.parametrize(
    "value",
    [
        "not-a-date",
        "2024/01/01",
        "01-01-2024",
        "garbage+1000",  # tz suffix stripped, "garbage" still invalid
        "T12:00:00",  # missing date
    ],
)
def test_parse_datetime_invalid_raises(value):
    with pytest.raises(NEM12ParseError):
        _parse_datetime(value)


def test_parse_datetime_does_not_mistake_iso_dash_for_tz():
    """The tz-stripping regex must not strip the ``-`` from an ISO date."""
    # 2024-01-01 ends with "-01" (3 chars). The regex requires 4 or 6
    # characters of offset, so this must NOT trigger stripping.
    assert _parse_datetime("2024-01-01") == datetime(2024, 1, 1)
