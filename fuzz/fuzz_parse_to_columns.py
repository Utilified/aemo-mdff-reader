"""Fuzz the columnar fast-path build."""

from __future__ import annotations

import io
import sys

import atheris

with atheris.instrument_imports():
    from aemo_mdff_reader import parse_to_columns


def TestOneInput(data: bytes) -> None:
    # See fuzz_parse.py — broad except is intentional for a pure-Python
    # memory-safe target. We're hunting for hangs / pathological growth.
    try:
        text = data.decode("utf-8", errors="replace")
        parse_to_columns(io.StringIO(text))
    except Exception:
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
