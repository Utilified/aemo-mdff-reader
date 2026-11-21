#!/bin/bash -eu
# ClusterFuzzLite build script — installs the package and compiles each
# atheris harness in fuzz/ via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC/aemo-mdff-reader"
# Install the build backend from verified wheels, then build the local
# package without allowing pip to resolve any more dependencies.
pip3 install --no-cache-dir --require-hashes --no-deps --only-binary=:all: \
  -r requirements/fuzz-build.txt

wheel_dir=$(mktemp -d)
trap 'rm -rf "$wheel_dir"' EXIT
# --ignore-requires-python: the package declares requires-python >=3.12,
# but OSS-Fuzz's base-builder-python still ships 3.11 (latest as of
# 2026-07: 3.11.13), so the metadata check would abort the fuzz build.
# The library code itself remains 3.11-runnable — dropping 3.11 was a
# support/CI decision, not a syntax bump — so the harnesses still
# exercise the real parser. Drop this flag once upstream ships 3.12.
pip3 wheel --no-deps --no-build-isolation --no-index --ignore-requires-python \
  --wheel-dir "$wheel_dir" .
pip3 install --no-deps --no-index --ignore-requires-python "$wheel_dir"/*.whl

for fuzzer in fuzz/fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
