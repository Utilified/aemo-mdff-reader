# ClusterFuzzLite build image for aemo-mdff-reader.
# Uses the OSS-Fuzz Python base image, which provides atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 (closes Scorecard PinnedDependenciesID); Dependabot's
# docker ecosystem keeps the digest fresh.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:ef0903c727eede93baa266d3ba12bb5f0329596201bad7bcd68de47b7cf9574d

COPY . $SRC/aemo-mdff-reader
WORKDIR $SRC/aemo-mdff-reader
COPY .clusterfuzzlite/build.sh $SRC/build.sh
