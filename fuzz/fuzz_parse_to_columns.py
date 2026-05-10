"""Fuzz the columnar fast-path build."""

from __future__ import annotations

import csv
import io
import sys

import atheris

with atheris.instrument_imports():
    from aemo_mdff_reader import parse_to_columns
    from aemo_mdff_reader.parser import NEM12ParseError


_EXPECTED = (
    NEM12ParseError,
    csv.Error,
    ValueError,
    IndexError,
    KeyError,
    OverflowError,
    UnicodeDecodeError,
)


def TestOneInput(data: bytes) -> None:
    try:
        text = data.decode("utf-8", errors="replace")
        parse_to_columns(io.StringIO(text))
    except _EXPECTED:
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
