#!/bin/bash -eu
# ClusterFuzzLite build script — installs the package and compiles each
# atheris harness in fuzz/ via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC/aemo-mdff-reader"
pip3 install --no-cache-dir .

for fuzzer in fuzz/fuzz_*.py; do
  name="$(basename "$fuzzer" .py)"
  compile_python_fuzzer "$fuzzer" --add-binary="${name}":"${name}"
done
