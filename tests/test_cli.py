"""Tests for the ``aemo-mdff-reader`` CLI."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from aemo_mdff_reader.cli import main

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


def test_cli_missing_input_returns_nonzero(tmp_path):
    out = tmp_path / "out.csv"
    with pytest.raises(FileNotFoundError):
        main([str(tmp_path / "nope.csv"), "-o", str(out)])


def test_cli_invalid_format_argument():
    with pytest.raises(SystemExit):
        main([str(FIXTURE), "--format", "yaml"])


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "aemo-mdff-reader" in out


def test_cli_parquet_output(tmp_path):
    pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    out = tmp_path / "out.parquet"
    rc = main([str(FIXTURE), "-o", str(out), "--format", "parquet"])
    assert rc == 0
    assert out.exists()
    import pandas as pd

    df = pd.read_parquet(out)
    assert len(df) == 3 * 48
    assert "NMI" in df.columns


def test_cli_parquet_accumulations(tmp_path):
    pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    nem13 = Path(__file__).parent / "fixtures" / "sample_nem13.csv"
    out = tmp_path / "acc.parquet"
    rc = main([str(nem13), "-o", str(out), "--records", "accumulations", "--format", "parquet"])
    assert rc == 0
    import pandas as pd

    df = pd.read_parquet(out)
    assert len(df) == 3
    assert "Quantity" in df.columns


def test_cli_parquet_without_pandas(monkeypatch, tmp_path, capsys):
    """The parquet path returns 2 with a clear error if pandas is missing."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError("test: pandas not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    rc = main([str(FIXTURE), "-o", str(tmp_path / "x.parquet"), "--format", "parquet"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "pandas" in err
