# ClusterFuzzLite build image for aemo-mdff-reader.
# Uses the OSS-Fuzz Python base image, which provides atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 (closes Scorecard PinnedDependenciesID); Dependabot's
# docker ecosystem keeps the digest fresh.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:1721fd6c14317227ea8de27748dc07d447bf67e1abfabecda3b75cc84fdaf5e2

COPY . $SRC/aemo-mdff-reader
WORKDIR $SRC/aemo-mdff-reader
COPY .clusterfuzzlite/build.sh $SRC/build.sh
