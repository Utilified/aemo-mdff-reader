#!/bin/bash -eu
# ClusterFuzzLite build script — installs the package and compiles each
# atheris harness in fuzz/ via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC/aemo-mdff-reader"
# --ignore-requires-python: the package declares requires-python >=3.12,
# but OSS-Fuzz's base-builder-python still ships 3.11 (latest as of
# 2026-07: 3.11.13), so the metadata check would abort the fuzz build.
# The library code itself remains 3.11-runnable — dropping 3.11 was a
# support/CI decision, not a syntax bump — so the harnesses still
# exercise the real parser. Drop this flag once upstream ships 3.12.
pip3 install --no-cache-dir --ignore-requires-python .

for fuzzer in fuzz/fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
