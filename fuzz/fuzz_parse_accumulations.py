"""Fuzz the NEM13 (accumulation) parser."""

from __future__ import annotations

import io
import sys

import atheris

with atheris.instrument_imports():
    from aemo_mdff_reader import parse_accumulations
    from aemo_mdff_reader.parser import NEM12ParseError


def TestOneInput(data: bytes) -> None:
    try:
        text = data.decode("utf-8", errors="replace")
        for _ in parse_accumulations(io.StringIO(text)):
            pass
    except (NEM12ParseError, ValueError, IndexError, KeyError, UnicodeDecodeError):
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
