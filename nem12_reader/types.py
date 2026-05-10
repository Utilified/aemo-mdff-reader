"""Lightweight data classes for parsed NEM12/NEM13 records.

These types form the public surface of the streaming parser. They use
``__slots__`` to keep per-row memory and allocation cost low when
processing large files (millions of intervals).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional


class Header:
    """100 record — file header."""

    __slots__ = ("datetime", "from_participant", "to_participant", "version")

    def __init__(
        self,
        version: str,
        datetime: Optional[datetime],
        from_participant: str,
        to_participant: str,
    ) -> None:
        self.version = version
        self.datetime = datetime
        self.from_participant = from_participant
        self.to_participant = to_participant

    def __repr__(self) -> str:
        return (
            f"Header(version={self.version!r}, datetime={self.datetime!r}, "
            f"from_participant={self.from_participant!r}, "
            f"to_participant={self.to_participant!r})"
        )


class NMIDetails:
    """200 record — NMI / channel details."""

    __slots__ = (
        "interval_length",
        "mdm_data_stream_identifier",
        "meter_serial_number",
        "next_scheduled_read_date",
        "nmi",
        "nmi_configuration",
        "nmi_suffix",
        "register_id",
        "uom",
    )

    def __init__(
        self,
        nmi: str,
        nmi_configuration: str,
        register_id: str,
        nmi_suffix: str,
        mdm_data_stream_identifier: str,
        meter_serial_number: str,
        uom: str,
        interval_length: int,
        next_scheduled_read_date: Optional[datetime],
    ) -> None:
        self.nmi = nmi
        self.nmi_configuration = nmi_configuration
        self.register_id = register_id
        self.nmi_suffix = nmi_suffix
        self.mdm_data_stream_identifier = mdm_data_stream_identifier
        self.meter_serial_number = meter_serial_number
        self.uom = uom
        self.interval_length = interval_length
        self.next_scheduled_read_date = next_scheduled_read_date


class IntervalReading:
    """A single interval reading — one cell of a 300 record.

    Notes
    -----
    ``value`` is always a ``float``. Empty cells in the source NEM12
    file are coerced to ``0.0`` so a single missing cell does not fail
    an entire row. Use ``quality_method`` (e.g. ``"S"`` for substituted,
    ``"F"`` for failed, ``"N"`` for null) to distinguish a real zero
    from a missing reading.
    """

    __slots__ = (
        "interval_date",
        "interval_end",
        "interval_index",
        "interval_length",
        "interval_start",
        "meter_serial_number",
        "msats_load_datetime",
        "nmi",
        "nmi_suffix",
        "quality_method",
        "reason_code",
        "reason_description",
        "register_id",
        "uom",
        "update_datetime",
        "value",
    )

    def __init__(
        self,
        nmi: str,
        meter_serial_number: str,
        register_id: str,
        nmi_suffix: str,
        uom: str,
        interval_length: int,
        interval_date: datetime,
        interval_start: datetime,
        interval_end: datetime,
        interval_index: int,
        value: float,
        quality_method: str,
        reason_code: Optional[int],
        reason_description: str,
        update_datetime: Optional[datetime],
        msats_load_datetime: Optional[datetime],
    ) -> None:
        self.nmi = nmi
        self.meter_serial_number = meter_serial_number
        self.register_id = register_id
        self.nmi_suffix = nmi_suffix
        self.uom = uom
        self.interval_length = interval_length
        self.interval_date = interval_date
        self.interval_start = interval_start
        self.interval_end = interval_end
        self.interval_index = interval_index
        self.value = value
        self.quality_method = quality_method
        self.reason_code = reason_code
        self.reason_description = reason_description
        self.update_datetime = update_datetime
        self.msats_load_datetime = msats_load_datetime


class IntervalEvent:
    """400 record — quality/event flag covering a range of intervals."""

    __slots__ = (
        "end_interval",
        "interval_date",
        "meter_serial_number",
        "nmi",
        "quality_method",
        "reason_code",
        "reason_description",
        "register_id",
        "start_interval",
    )

    def __init__(
        self,
        nmi: str,
        meter_serial_number: str,
        register_id: str,
        interval_date: datetime,
        start_interval: int,
        end_interval: int,
        quality_method: str,
        reason_code: Optional[int],
        reason_description: str,
    ) -> None:
        self.nmi = nmi
        self.meter_serial_number = meter_serial_number
        self.register_id = register_id
        self.interval_date = interval_date
        self.start_interval = start_interval
        self.end_interval = end_interval
        self.quality_method = quality_method
        self.reason_code = reason_code
        self.reason_description = reason_description


class AccumulationReading:
    """250 record — NEM13 NMI accumulation / manual-read data.

    Each 250 record represents a previous + current register read pair
    plus a calculated quantity (consumption between the two reads).
    """

    __slots__ = (
        "current_quality_method",
        "current_reason_code",
        "current_reason_description",
        "current_register_read",
        "current_register_read_datetime",
        "direction_indicator",
        "mdm_data_stream_identifier",
        "meter_serial_number",
        "msats_load_datetime",
        "next_scheduled_read_date",
        "nmi",
        "nmi_configuration",
        "nmi_suffix",
        "previous_quality_method",
        "previous_reason_code",
        "previous_reason_description",
        "previous_register_read",
        "previous_register_read_datetime",
        "quantity",
        "register_id",
        "uom",
        "update_datetime",
    )

    def __init__(
        self,
        nmi: str,
        nmi_configuration: str,
        register_id: str,
        nmi_suffix: str,
        mdm_data_stream_identifier: str,
        meter_serial_number: str,
        direction_indicator: str,
        previous_register_read: float,
        previous_register_read_datetime: Optional[datetime],
        previous_quality_method: str,
        previous_reason_code: Optional[int],
        previous_reason_description: str,
        current_register_read: float,
        current_register_read_datetime: Optional[datetime],
        current_quality_method: str,
        current_reason_code: Optional[int],
        current_reason_description: str,
        quantity: float,
        uom: str,
        next_scheduled_read_date: Optional[datetime],
        update_datetime: Optional[datetime],
        msats_load_datetime: Optional[datetime],
    ) -> None:
        self.nmi = nmi
        self.nmi_configuration = nmi_configuration
        self.register_id = register_id
        self.nmi_suffix = nmi_suffix
        self.mdm_data_stream_identifier = mdm_data_stream_identifier
        self.meter_serial_number = meter_serial_number
        self.direction_indicator = direction_indicator
        self.previous_register_read = previous_register_read
        self.previous_register_read_datetime = previous_register_read_datetime
        self.previous_quality_method = previous_quality_method
        self.previous_reason_code = previous_reason_code
        self.previous_reason_description = previous_reason_description
        self.current_register_read = current_register_read
        self.current_register_read_datetime = current_register_read_datetime
        self.current_quality_method = current_quality_method
        self.current_reason_code = current_reason_code
        self.current_reason_description = current_reason_description
        self.quantity = quantity
        self.uom = uom
        self.next_scheduled_read_date = next_scheduled_read_date
        self.update_datetime = update_datetime
        self.msats_load_datetime = msats_load_datetime


class B2BDetails:
    """500 (NEM12) / 550 (NEM13) record — B2B transaction details.

    The 500 record carries a single transaction (TransCode +
    RetServiceOrder + ReadDateTime + IndexRead). The 550 record carries
    a paired previous/current transaction. We surface them with the
    same class and a ``record_kind`` discriminator (``"500"`` or
    ``"550"``) so callers can branch when needed.

    Fields that do not apply to the current ``record_kind`` are set to
    ``None`` (not ``""``), so callers can distinguish "structurally
    absent for this record kind" from "present but empty in source"::

        if b.record_kind == "550":
            assert b.previous_trans_code is not None  # set
            assert b.trans_code is None                # not in this kind
    """

    __slots__ = (
        "current_ret_service_order",
        "current_trans_code",
        "index_read",
        "previous_ret_service_order",
        "previous_trans_code",
        "read_datetime",
        "record_kind",
        "ret_service_order",
        "trans_code",
    )

    def __init__(
        self,
        record_kind: str,
        trans_code: Optional[str] = None,
        ret_service_order: Optional[str] = None,
        read_datetime: Optional[datetime] = None,
        index_read: Optional[str] = None,
        previous_trans_code: Optional[str] = None,
        previous_ret_service_order: Optional[str] = None,
        current_trans_code: Optional[str] = None,
        current_ret_service_order: Optional[str] = None,
    ) -> None:
        self.record_kind = record_kind
        self.trans_code = trans_code
        self.ret_service_order = ret_service_order
        self.read_datetime = read_datetime
        self.index_read = index_read
        self.previous_trans_code = previous_trans_code
        self.previous_ret_service_order = previous_ret_service_order
        self.current_trans_code = current_trans_code
        self.current_ret_service_order = current_ret_service_order


__all__ = [
    "AccumulationReading",
    "B2BDetails",
    "Header",
    "IntervalEvent",
    "IntervalReading",
    "NMIDetails",
]
