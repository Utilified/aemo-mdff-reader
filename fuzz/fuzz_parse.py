"""Fuzz the NEM12 streaming parser entry point.

Run locally:
    pip install atheris
    python fuzz/fuzz_parse.py -atheris_runs=10000

Run in OSS-Fuzz / ClusterFuzzLite: this file is built by
.clusterfuzzlite/build.sh.
"""

from __future__ import annotations

import csv
import io
import sys

import atheris

with atheris.instrument_imports():
    from aemo_mdff_reader import parse
    from aemo_mdff_reader.parser import NEM12ParseError


# Exceptions the parser is allowed to raise on malformed input. Anything
# else (AttributeError, TypeError, RecursionError, …) escapes and is
# reported as a bug.
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
        for _ in parse(io.StringIO(text)):
            pass
    except _EXPECTED:
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
