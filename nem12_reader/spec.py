"""Constants from the AEMO MDFF specification (NEM12 / NEM13).

This module mirrors the enumerations and allowed-value lists in the
AEMO Meter Data File Format Specification — NEM12 & NEM13, v2.6,
effective 29 September 2024. The spec is the source of truth; this
module is a convenience surface for callers who want to validate
parsed records against it.

The parser itself does not enforce these enumerations strictly — it
accepts any well-formed CSV — so downstream code is free to apply as
much or as little validation as it needs.

Reference (always points at the current AEMO publication):
https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/market-operations/retail-and-metering/metering-procedures-guidelines-and-processes
"""

from __future__ import annotations

from typing import Dict, FrozenSet

SPEC_VERSION = "2.6"
SPEC_EFFECTIVE_DATE = "2024-09-29"
SPEC_DOCUMENT_TITLE = "Meter Data File Format Specification NEM12 & NEM13"
SPEC_URL = (
    "https://www.aemo.com.au/energy-systems/electricity/"
    "national-electricity-market-nem/market-operations/retail-and-metering/"
    "metering-procedures-guidelines-and-processes"
)


# -- Section 4.3, NMI data details (200) ------------------------------------

#: IntervalLength values permitted by the spec, in minutes.
#: The parser also accepts other divisors of 1440 (e.g. 1, 60) for tolerance
#: with non-conforming files; pass through this constant if you want to
#: reject anything outside the spec.
ALLOWED_INTERVAL_LENGTHS: FrozenSet[int] = frozenset({5, 15, 30})


# -- Section 5.3, Accumulation meter data (250) -----------------------------

#: DirectionIndicator allowed values per the spec.
DIRECTION_INDICATORS: Dict[str, str] = {
    "I": "Import (energy flows from the connection point to the grid)",
    "E": "Export (energy flows from the grid to the connection point)",
}


# -- Appendix A, Transaction code flags (500 / 550) -------------------------

TRANSACTION_CODES: Dict[str, str] = {
    "A": "Alteration",
    "C": "Meter Reconfiguration",
    "G": "Re-energisation",
    "D": "De-energisation",
    "E": "Estimate",
    "N": "Normal Read",
    "O": "Other (use when the original TransCode is unavailable, e.g. Historical Data)",
    "S": "Special Read",
    "R": "Removal of meter",
}


# -- Appendix B, allowed UOM values -----------------------------------------

#: Units of measure allowed in the UOM field. Comparison is case-insensitive
#: per the spec, so callers should normalise before lookup.
UOM_VALUES: FrozenSet[str] = frozenset(
    {
        "MWh",
        "kWh",
        "Wh",
        "MVArh",
        "kVArh",
        "VArh",
        "MVAr",
        "kVAr",
        "VAr",
        "MW",
        "kW",
        "W",
        "MVAh",
        "kVAh",
        "VAh",
        "MVA",
        "kVA",
        "VA",
        "kV",
        "V",
        "kA",
        "A",
        "pf",
    }
)


# -- Appendix C, Quality flags ----------------------------------------------

QUALITY_FLAGS: Dict[str, str] = {
    "A": "Actual Metering Data (no method flag required)",
    "E": "Forward estimated data (method flag required, no reason code)",
    "F": "Final substituted data (method flag and reason code required)",
    "S": "Substituted data (method flag and reason code required)",
    "V": (
        "Variable data — only valid as the QualityMethod of a 300 record "
        "to indicate that 400 rows carry per-interval flags. Not valid in "
        "NEM13 files."
    ),
}


# -- Appendix E, current reason codes ---------------------------------------

REASON_CODES: Dict[int, str] = {
    0: "Free text description",
    1: "Meter/equipment changed",
    2: "Extreme weather conditions",
    3: "Quarantined premises",
    5: "Blank screen",
    6: "De-energised premises",
    7: "Unable to locate meter",
    8: "Vacant premises",
    9: "Under investigation",
    10: "Lock damaged unable to open",
    11: "In wrong route",
    12: "Locked premises",
    13: "Locked gate",
    14: "Locked meter box",
    15: "Overgrown vegetation",
    17: "Unsafe equipment/location",
    18: "Read less than previous",
    20: "Damaged equipment/panel",
    21: "Main switch off",
    22: "Meter/equipment seals missing",
    23: "Reader error",
    24: "Substituted/replaced data (data correction)",
    25: "Unable to locate premises",
    26: "Negative consumption (generation)",
    27: "RoLR",
    28: "CT/VT fault",
    29: "Relay faulty/damaged",
    31: "Not all meters read",
    32: "Re-energised without readings",
    33: "De-energised without readings",
    34: "Meter not in handheld",
    35: "Timeswitch faulty/reset required",
    36: "Meter high/ladder required",
    37: "Meter under churn",
    38: "Unmarried lock",
    39: "Reverse energy observed",
    40: "Unrestrained livestock",
    41: "Faulty Meter display/dials",
    42: "Channel added/removed",
    43: "Power outage",
    44: "Meter testing",
    45: "Readings failed to validate",
    47: "Refused access",
    48: "Dog on premises",
    51: "Installation demolished",
    52: "Access — blocked",
    53: "Pests in meter box",
    54: "Meter box damaged/faulty",
    55: "Dials obscured",
    60: "Illegal connection",
    61: "Equipment tampered",
    62: "NSRD window expired",
    64: "Key required",
    65: "Wrong key provided",
    67: "Transfer",
    68: "Zero consumption",
    69: "Reading exceeds Substitute",
    71: "Probe read error",
    72: "Re-calculated based on Actual Metering Data",
    73: "Low consumption",
    74: "High consumption",
    75: "Customer read",
    76: "Communications fault",
    77: "Estimation Forecast",
    78: "Null Data",
    79: "Power Outage Alarm",
    80: "Short Interval Alarm",
    81: "Long Interval Alarm",
    87: "Reset occurred",
    89: "Time reset occurred",
    # Added in v2.6 (ICF_054 substitution type review, July 2023 REMP):
    100: "Incorrect Meter Multiplier",
    101: "Temporarily Connection Point unmetered",
    102: "Customer By-Pass",
    103: "Network By-Pass",
    104: "Transposed Channel",
    105: "Transposed Channel — UoM Correction",
    106: "Transposed Channel — Reverse Polarity",
    107: "Transposed Meter",
    108: "Network by-pass extreme weather",
    109: "Defined load method",
}


# -- Appendix F, obsolete reason codes (Historical Data only) ---------------

OBSOLETE_REASON_CODES: Dict[int, str] = {
    4: "Dangerous dog",
    16: "Noxious weeds at premises preventing access",
    19: "Consumer wanted",
    30: "Meter stop switch on",
    46: "Extreme weather/hot",
    49: "Wet paint",
    50: "Wrong tariff",
    58: "Meter ok — supply failure",
    70: "Probe reports tampering",
    82: "CRC error",
    83: "RAM checksum error",
    84: "ROM checksum error",
    85: "Data missing alarm",
    86: "Clock error alarm",
    88: "Watchdog timeout alarm",
    90: "Test mode",
    91: "Load control",
    92: "Added interval (data correction)",
    93: "Replaced interval (data correction)",
    94: "Estimated interval (data correction)",
    95: "Pulse overflow alarm",
    96: "Data out of limits",
    97: "Excluded data",
    98: "Parity error",
    99: "Energy type (register changed)",
}


__all__ = [
    "ALLOWED_INTERVAL_LENGTHS",
    "DIRECTION_INDICATORS",
    "OBSOLETE_REASON_CODES",
    "QUALITY_FLAGS",
    "REASON_CODES",
    "SPEC_DOCUMENT_TITLE",
    "SPEC_EFFECTIVE_DATE",
    "SPEC_URL",
    "SPEC_VERSION",
    "TRANSACTION_CODES",
    "UOM_VALUES",
]
