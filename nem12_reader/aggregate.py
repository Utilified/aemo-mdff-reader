"""Post-parse aggregation helpers.

Lightweight composable iterators for the most common downstream
operations on parsed NEM12 data: grouping by NMI/channel, and rolling
intervals up to daily totals. Each function takes any iterable of
:class:`IntervalReading` objects, so they compose with :func:`parse`,
``parse_to_columns``, and the buffered :class:`NEMReader` facade.

>>> from nem12_reader import parse
>>> from nem12_reader.aggregate import daily_totals
>>> for d in daily_totals(parse("metering.csv")):
...     print(d.nmi, d.register_id, d.interval_date, d.total)
"""

from __future__ import annotations

import itertools
from datetime import datetime
from typing import Iterable, Iterator, NamedTuple, Optional, Tuple

from .types import IntervalReading


class ChannelKey(NamedTuple):
    """Composite key identifying a single metering channel."""

    nmi: str
    register_id: str
    nmi_suffix: str


class DailyTotal(NamedTuple):
    """A single channel's total energy / quantity for a calendar day.

    ``total`` is the sum of ``IntervalReading.value`` for every reading
    that fell on ``interval_date``. ``interval_count`` is the number of
    readings summed (useful for spotting partial days). ``unique_quality_flags``
    is the set of distinct 1-character quality flags seen — a single
    ``{"A"}`` means the day is fully Actual, anything else hints at
    substituted or estimated data.
    """

    nmi: str
    register_id: str
    nmi_suffix: str
    uom: str
    interval_date: datetime
    total: float
    interval_count: int
    unique_quality_flags: frozenset[str]


def group_by_nmi(
    readings: Iterable[IntervalReading],
) -> Iterator[Tuple[ChannelKey, Iterator[IntervalReading]]]:
    """Yield ``(ChannelKey, group)`` pairs, one per (NMI, register, suffix).

    NEM12 files are emitted in 200-record blocks: every 300 row inside
    a block shares the same NMI / register / suffix, and a new 200 row
    starts a new block. We use :func:`itertools.groupby` over those
    fields, which means each ``group`` iterator must be consumed before
    the next pair is requested — exactly the same contract as
    ``itertools.groupby``.

    For a materialised list per group, wrap the inner iterator::

        for key, group in group_by_nmi(parse(path)):
            rows = list(group)
            ...
    """

    def _key(r: IntervalReading) -> ChannelKey:
        return ChannelKey(r.nmi, r.register_id, r.nmi_suffix)

    yield from itertools.groupby(readings, key=_key)


def daily_totals(readings: Iterable[IntervalReading]) -> Iterator[DailyTotal]:
    """Yield one :class:`DailyTotal` per (channel, calendar day).

    Within each 300 row, all readings share the same ``interval_date``
    and the parser emits them contiguously, so the rollup is a streaming
    O(1)-memory operation: we accumulate while ``(channel, date)`` stays
    constant and emit when it changes.

    Empty cells in the source are coerced to ``0.0`` upstream (see
    :class:`IntervalReading`); they are summed as zero.
    """
    current_key: Optional[Tuple[ChannelKey, datetime]] = None
    current_uom: str = ""
    total = 0.0
    count = 0
    flags: set[str] = set()

    for r in readings:
        key = (ChannelKey(r.nmi, r.register_id, r.nmi_suffix), r.interval_date)
        if current_key is None:
            current_key = key
            current_uom = r.uom
        elif key != current_key:
            yield DailyTotal(
                nmi=current_key[0].nmi,
                register_id=current_key[0].register_id,
                nmi_suffix=current_key[0].nmi_suffix,
                uom=current_uom,
                interval_date=current_key[1],
                total=total,
                interval_count=count,
                unique_quality_flags=frozenset(flags),
            )
            current_key = key
            current_uom = r.uom
            total = 0.0
            count = 0
            flags = set()
        total += r.value
        count += 1
        if r.quality_method:
            flags.add(r.quality_method[:1])

    if current_key is not None:
        yield DailyTotal(
            nmi=current_key[0].nmi,
            register_id=current_key[0].register_id,
            nmi_suffix=current_key[0].nmi_suffix,
            uom=current_uom,
            interval_date=current_key[1],
            total=total,
            interval_count=count,
            unique_quality_flags=frozenset(flags),
        )


__all__ = [
    "ChannelKey",
    "DailyTotal",
    "daily_totals",
    "group_by_nmi",
]
