"""Tests for the ``nem12-reader`` CLI."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

from nem12_reader.cli import main


FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem12.csv"


def test_cli_csv_output_to_file(tmp_path):
    out = tmp_path / "out.csv"
    rc = main([str(FIXTURE), "-o", str(out)])
    assert rc == 0
    rows = list(csv.reader(out.open()))
    # header + 3 × 48 rows
    assert len(rows) == 1 + 3 * 48
    assert rows[0][0] == "NMI"


def test_cli_csv_output_to_stdout(capsys):
    rc = main([str(FIXTURE)])
    assert rc == 0
    captured = capsys.readouterr().out
    lines = captured.splitlines()
    assert lines[0].startswith("NMI,")
    assert len(lines) == 1 + 3 * 48
