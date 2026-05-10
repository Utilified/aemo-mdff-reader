"""Fuzz the NEM12 streaming parser entry point.

Run locally:
    pip install atheris
    python fuzz/fuzz_parse.py -atheris_runs=10000

Run in OSS-Fuzz / ClusterFuzzLite: this file is built by
.clusterfuzzlite/build.sh.
"""

from __future__ import annotations

import io
import sys

import atheris

with atheris.instrument_imports():
    from aemo_mdff_reader import parse


def TestOneInput(data: bytes) -> None:
    # Python is memory-safe, so coverage-guided fuzzing of a pure-Python
    # parser is hunting for hangs, infinite loops, and pathological
    # memory growth — not crashes. Any exception raised by the parser
    # on malformed input is by definition an expected rejection, so we
    # swallow them broadly. SystemExit / KeyboardInterrupt deliberately
    # propagate.
    try:
        text = data.decode("utf-8", errors="replace")
        for _ in parse(io.StringIO(text)):
            pass
    except Exception:  # see comment above.
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
