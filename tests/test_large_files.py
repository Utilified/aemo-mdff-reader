"""Tests for the bounded-memory streaming helpers.

iter_chunks, iter_dataframes, iter_columns_chunks all promise
O(chunk_size) memory regardless of source size — verify they batch
correctly and accept the same source variants as ``parse``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nem12_reader import (
    iter_columns_chunks,
    iter_dataframes,
    parse,
)
from nem12_reader.aggregate import iter_chunks

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nem12.csv"


# ---------------------------------------------------------------------------
# iter_chunks
# ---------------------------------------------------------------------------


def test_iter_chunks_partitions_evenly():
    out = list(iter_chunks(range(10), 3))
    assert out == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_iter_chunks_with_size_larger_than_input():
    out = list(iter_chunks(range(3), 100))
    assert out == [[0, 1, 2]]


def test_iter_chunks_empty_input_yields_nothing():
    assert list(iter_chunks([], 10)) == []


@pytest.mark.parametrize("size", [0, -1, -100])
def test_iter_chunks_rejects_non_positive_size(size):
    with pytest.raises(ValueError):
        list(iter_chunks(range(10), size))


def test_iter_chunks_is_streaming():
    # The chunker should consume one batch at a time. We verify by
    # passing a generator that records how far it's been advanced when
    # we receive each batch.
    consumed = 0

    def source():
        nonlocal consumed
        for i in range(7):
            consumed = i + 1
            yield i

    it = iter_chunks(source(), 3)
    first = next(it)
    assert first == [0, 1, 2]
    assert consumed == 3, "should not have read past the first batch"
    second = next(it)
    assert second == [3, 4, 5]
    assert consumed == 6


def test_iter_chunks_over_parsed_readings():
    # Real round-trip: chunk parsed readings into 50-row batches and
    # confirm the totals match.
    batches = list(iter_chunks(parse(FIXTURE), 50))
    total = sum(len(b) for b in batches)
    assert total == 3 * 48
    # 50, 50, 44 — last batch shorter than the chunk size.
    assert [len(b) for b in batches] == [50, 50, 44]


# ---------------------------------------------------------------------------
# iter_dataframes
# ---------------------------------------------------------------------------


def test_iter_dataframes_yields_dataframes_of_chunk_size():
    pd = pytest.importorskip("pandas")
    chunks = list(iter_dataframes(FIXTURE, chunk_size=50))
    assert all(isinstance(df, pd.DataFrame) for df in chunks)
    assert [len(df) for df in chunks] == [50, 50, 44]


def test_iter_dataframes_concat_matches_to_dataframe():
    pd = pytest.importorskip("pandas")
    from nem12_reader import to_dataframe

    chunked = pd.concat(list(iter_dataframes(FIXTURE, chunk_size=30)), ignore_index=True)
    bulk = to_dataframe(FIXTURE)
    # Same row count and same data — pandas equality covers the schema.
    assert len(chunked) == len(bulk)
    pd.testing.assert_frame_equal(
        chunked.sort_values(list(bulk.columns)).reset_index(drop=True),
        bulk.sort_values(list(bulk.columns)).reset_index(drop=True),
    )


def test_iter_dataframes_accepts_iterable_of_readings():
    pytest.importorskip("pandas")
    readings = list(parse(FIXTURE))
    chunks = list(iter_dataframes(readings, chunk_size=72))
    assert sum(len(df) for df in chunks) == len(readings)


# ---------------------------------------------------------------------------
# iter_columns_chunks
# ---------------------------------------------------------------------------


def test_iter_columns_chunks_yields_dict_chunks():
    chunks = list(iter_columns_chunks(FIXTURE, chunk_size=50))
    assert [len(c["NMI"]) for c in chunks] == [50, 50, 44]
    # Every column in every chunk has the same length.
    for c in chunks:
        n = len(c["NMI"])
        assert all(len(v) == n for v in c.values())


def test_iter_columns_chunks_concat_matches_parse_to_columns():
    from nem12_reader import parse_to_columns

    chunks = list(iter_columns_chunks(FIXTURE, chunk_size=37))
    full = parse_to_columns(FIXTURE)
    for col in full:
        joined: list = []
        for c in chunks:
            joined.extend(c[col])
        assert joined == full[col], col
