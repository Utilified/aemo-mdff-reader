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

    __slots__ = ("version", "datetime", "from_participant", "to_participant")

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
        "nmi",
        "nmi_configuration",
        "register_id",
        "nmi_suffix",
        "mdm_data_stream_identifier",
        "meter_serial_number",
        "uom",
        "interval_length",
        "next_scheduled_read_date",
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
    """A single interval reading — one cell of a 300 record."""

    __slots__ = (
        "nmi",
        "meter_serial_number",
        "register_id",
        "nmi_suffix",
        "uom",
        "interval_length",
        "interval_date",
        "interval_start",
        "interval_end",
        "interval_index",
        "value",
        "quality_method",
        "reason_code",
        "reason_description",
        "update_datetime",
        "msats_load_datetime",
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
        "nmi",
        "meter_serial_number",
        "register_id",
        "interval_date",
        "start_interval",
        "end_interval",
        "quality_method",
        "reason_code",
        "reason_description",
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


__all__ = [
    "Header",
    "NMIDetails",
    "IntervalReading",
    "IntervalEvent",
]
