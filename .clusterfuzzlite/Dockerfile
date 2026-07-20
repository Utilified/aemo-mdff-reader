# ClusterFuzzLite build image for aemo-mdff-reader.
# Uses the OSS-Fuzz Python base image, which provides atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 (closes Scorecard PinnedDependenciesID); Dependabot's
# docker ecosystem keeps the digest fresh.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:d4ef5a787f3e1a420721da74823202185dc04e2e792984671c31a67d7ce66832

COPY . $SRC/aemo-mdff-reader
WORKDIR $SRC/aemo-mdff-reader
COPY .clusterfuzzlite/build.sh $SRC/build.sh
