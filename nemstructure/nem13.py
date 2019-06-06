"NMI data details record for nem-reader-imported"
# import statements
from nemstructure.record import Record, MANDATORY, REQUIRED, NOTREQUIRED
ATTRIBUTES = {}

ACCUMULATION_RECORD_ID = 250
ATTRIBUTES[ACCUMULATION_RECORD_ID] = [
    ("RecordIndicator", MANDATORY),
    ("NMI", MANDATORY),
    ("NMIConfiguration", MANDATORY),
    ("RegisterID", MANDATORY),
    ("NMISuffix", MANDATORY),
    ("MDMDataStreamIdentifier", NOTREQUIRED),
    ("MeterSerialNumber", MANDATORY),
    ("DirectionIndicator", MANDATORY),
    ("PreviousRegisterRead", MANDATORY),
    ("PreviousQualityMethod", MANDATORY),
    ("PreviousReasonCode", NOTREQUIRED),
    ("PreviousReasonDescription", NOTREQUIRED),
    ("CurrentRegisterRead", MANDATORY),
    ("CurrentRegisterReadDateTime", MANDATORY),
    ("CurrentQualityMethod", MANDATORY),
    ("CurrentReasonCode", NOTREQUIRED),
    ("CurrentReasonDescription", NOTREQUIRED),
    ("Quantity", MANDATORY),
    ("UOM", MANDATORY),
    ("NextScheduledReadDate", NOTREQUIRED),
    ("UpdateDateTime", NOTREQUIRED),
    ("MSATSLoadDateTime", REQUIRED)
]

B2B_RECORD_ID = 550
ATTRIBUTES[B2B_RECORD_ID] = [
    ("RecordIndicator", MANDATORY),
    ("PreviousTransCode", MANDATORY),
    ("PreviousRetServiceOrder", REQUIRED),
    ("CurrentTransCode", MANDATORY),
    ("CurrentRetServiceOrder", REQUIRED)
]

class AccummulationData(Record):
    """
    Represenents a NMI Data details record
    in the NEM-12 file.
    """
    def __init__(self):
        super().__init__(ACCUMULATION_RECORD_ID, ATTRIBUTES[ACCUMULATION_RECORD_ID])

class B2BDetails(Record):
    """
    Represenents a NMI Data details record
    in the NEM-12 file.
    """
    def __init__(self):
        super().__init__(ACCUMULATION_RECORD_ID, ATTRIBUTES[ACCUMULATION_RECORD_ID])
