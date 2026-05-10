"""Tests for NMI checksum + file validation utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from aemo_mdff_reader import nmi_checksum, validate_file, validate_nmi

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem12.csv"
NEM13_FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem13.csv"


def test_nmi_checksum_returns_single_digit():
    digit = nmi_checksum("NMI1234567")
    assert isinstance(digit, int)
    assert 0 <= digit <= 9


def test_nmi_checksum_is_deterministic():
    assert nmi_checksum("NMI1234567") == nmi_checksum("NMI1234567")


@pytest.mark.parametrize(
    "bad_nmi",
    ["", "TOOSHORT", "WAY_TOO_LONG_FOR_AN_NMI", "NMI 12345 ", "NMI\n123456"],
)
def test_nmi_checksum_rejects_malformed(bad_nmi):
    with pytest.raises(ValueError):
        nmi_checksum(bad_nmi)


def test_validate_nmi_structural():
    assert validate_nmi("NMI1234567") is True
    assert validate_nmi("TOO_SHORT") is False


def test_validate_nmi_with_explicit_checksum():
    correct = str(nmi_checksum("NMI1234567"))
    assert validate_nmi("NMI1234567", correct) is True
    wrong = str((int(correct) + 1) % 10)
    assert validate_nmi("NMI1234567", wrong) is False


def test_validate_nmi_with_invalid_nmi_returns_false():
    # Non-printable characters should fail validation, not raise.
    assert validate_nmi("\x00abcdefghi") is False


def test_validate_file_clean_fixture():
    issues = validate_file(FIXTURE)
    assert issues == []


def test_validate_file_clean_nem13_fixture():
    issues = validate_file(NEM13_FIXTURE)
    assert issues == []


def test_validate_file_missing_header():
    rows = [
        ["200", "NMI1234567", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "30", ""],
        ["300", "20240101"] + ["0.1"] * 48 + ["A", "", "", "", ""],
        ["900"],
    ]
    issues = validate_file(rows)
    assert any("100 header" in i for i in issues)


def test_validate_file_missing_footer():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "NMI1234567", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "30", ""],
        ["300", "20240101"] + ["0.1"] * 48 + ["A", "", "", "", ""],
    ]
    issues = validate_file(rows)
    assert any("900 footer" in i for i in issues)


def test_validate_file_300_before_200():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["300", "20240101"] + ["0.1"] * 48 + ["A", "", "", "", ""],
        ["900"],
    ]
    issues = validate_file(rows)
    assert any("300 row encountered before any 200" in i for i in issues)


def test_validate_file_short_250_row():
    rows = [
        ["100", "NEM13", "202401010000", "X", "Y"],
        ["250", "NMI1234567", "E1"],  # truncated
        ["900"],
    ]
    issues = validate_file(rows)
    assert any("250 row" in i for i in issues)


def test_validate_file_invalid_nmi_structure():
    rows = [
        ["100", "NEM12", "202401010000", "X", "Y"],
        ["200", "TOOSHORT", "E1Q1", "E1", "E1", "N1", "M1", "KWH", "30", ""],
        ["900"],
    ]
    issues = validate_file(rows)
    assert any("invalid structure" in i for i in issues)


def test_cli_validate_clean_file_returns_zero(capsys):
    from aemo_mdff_reader.cli import main

    rc = main([str(FIXTURE), "--validate"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "OK" in err


def test_cli_validate_broken_file_returns_one(tmp_path, capsys):
    from aemo_mdff_reader.cli import main

    bad = tmp_path / "broken.csv"
    bad.write_text("200,NMI1234567,E1Q1,E1,E1,N1,M1,KWH,30,\n")
    rc = main([str(bad), "--validate"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "100 header" in err or "900 footer" in err
