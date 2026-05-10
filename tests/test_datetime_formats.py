"""Datetime parser format coverage."""

from __future__ import annotations

from datetime import datetime

import pytest

from nem12_reader.parser import NEM12ParseError, _parse_datetime


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", None),
        ("20240101", datetime(2024, 1, 1)),
        ("20240101000000", datetime(2024, 1, 1, 0, 0, 0)),
        ("20240131123456", datetime(2024, 1, 31, 12, 34, 56)),
        ("202401312359", datetime(2024, 1, 31, 23, 59)),  # YYYYMMDDhhmm
        ("2024-02-29", datetime(2024, 2, 29)),  # ISO date — leap year
    ],
)
def test_parse_datetime_supported_formats(value, expected):
    assert _parse_datetime(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "not-a-date",
        "2024/01/01",
        "01-01-2024",
        "20240101T0000",
    ],
)
def test_parse_datetime_invalid_raises(value):
    with pytest.raises(NEM12ParseError):
        _parse_datetime(value)
