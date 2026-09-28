# ClusterFuzzLite build image for aemo-mdff-reader.
# Uses the OSS-Fuzz Python base image, which provides atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 (closes Scorecard PinnedDependenciesID); Dependabot's
# docker ecosystem keeps the digest fresh.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:6a90ec89a18436e057a06f54266c3f120eb87d96c095b0c67a2b15cab33ec1f4

COPY . $SRC/aemo-mdff-reader
WORKDIR $SRC/aemo-mdff-reader
COPY .clusterfuzzlite/build.sh $SRC/build.sh
