"""Tests for the AEMO MDFF v2.6 spec-constants module."""

from __future__ import annotations

import nem12_reader
from nem12_reader import spec


def test_spec_module_is_re_exported():
    """``nem12_reader.spec`` is part of the public API."""
    assert nem12_reader.spec is spec


def test_spec_version_metadata():
    assert spec.SPEC_VERSION == "2.6"
    # ISO-8601 effective date keeps callers parseable.
    assert spec.SPEC_EFFECTIVE_DATE == "2024-09-29"
    assert "Meter Data File Format" in spec.SPEC_DOCUMENT_TITLE
    assert spec.SPEC_URL.startswith("https://www.aemo.com.au")


def test_allowed_interval_lengths_match_spec():
    # MDFF v2.6 §4.3 — IntervalLength: 5, 15, or 30 minutes.
    assert spec.ALLOWED_INTERVAL_LENGTHS == frozenset({5, 15, 30})


def test_direction_indicators_match_spec():
    # MDFF v2.6 §5.3 — DirectionIndicator: I or E.
    assert set(spec.DIRECTION_INDICATORS) == {"I", "E"}


def test_transaction_codes_match_spec():
    # MDFF v2.6 Appendix A — A, C, G, D, E, N, O, S, R.
    assert set(spec.TRANSACTION_CODES) == {"A", "C", "G", "D", "E", "N", "O", "S", "R"}


def test_uom_values_include_common_units():
    # MDFF v2.6 Appendix B — case-insensitive set; spot-check the most
    # common metering units appear.
    for unit in ("kWh", "MWh", "Wh", "kVArh", "kW", "MW", "pf"):
        assert unit in spec.UOM_VALUES


def test_quality_flags_match_spec():
    # MDFF v2.6 Appendix C — A, E, F, S, V.
    assert set(spec.QUALITY_FLAGS) == {"A", "E", "F", "S", "V"}


def test_reason_codes_include_v2_6_additions():
    # MDFF v2.6 added codes 100-109 via ICF_054 / July 2023 REMP.
    for code in range(100, 110):
        assert code in spec.REASON_CODES, f"missing v2.6 reason code {code}"
    # Spot-check earlier codes are present too.
    assert spec.REASON_CODES[0] == "Free text description"
    assert spec.REASON_CODES[79] == "Power Outage Alarm"


def test_obsolete_reason_codes_are_not_in_active_set():
    # Appendix F codes are for Historical Data only and must not appear
    # in the active list.
    assert spec.OBSOLETE_REASON_CODES.keys().isdisjoint(spec.REASON_CODES.keys())
    # And the explicitly-named obsolete entries are present.
    for code in (4, 16, 19, 30, 46, 49, 50, 58, 70, 82, 83, 84, 85, 86, 88, 90):
        assert code in spec.OBSOLETE_REASON_CODES


def test_immutable_constants_are_actually_immutable():
    # Catch accidental mutation: the *_VALUES sets must be frozenset.
    assert isinstance(spec.ALLOWED_INTERVAL_LENGTHS, frozenset)
    assert isinstance(spec.UOM_VALUES, frozenset)
