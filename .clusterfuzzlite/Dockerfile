# ClusterFuzzLite build image for aemo-mdff-reader.
# Uses the OSS-Fuzz Python base image, which provides atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 (closes Scorecard PinnedDependenciesID); Dependabot's
# docker ecosystem keeps the digest fresh.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:88bcf57cb6507ccc95cb5fcc3afeece6278b24880ec483a17f044a154277f9d0

COPY . $SRC/aemo-mdff-reader
WORKDIR $SRC/aemo-mdff-reader
COPY .clusterfuzzlite/build.sh $SRC/build.sh
