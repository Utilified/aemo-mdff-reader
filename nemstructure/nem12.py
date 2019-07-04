"""NMI data details record for nem-reader-imported"""
# import statements
from nemstructure.record import Record, MANDATORY, REQUIRED, NOTREQUIRED
ATTRIBUTES = {}
MINUTES_DAILY = 24 * 60

NMI_RECORD_ID = 200
ATTRIBUTES[NMI_RECORD_ID] = [
    ("RecordIndicator", MANDATORY),
    ("NMI", MANDATORY),
    ("NMIConfiguration", MANDATORY),
    ("RegisterID", NOTREQUIRED),
    ("NMISuffix", MANDATORY),
    ("MDMDataStreamIdentifier", MANDATORY),
    ("MeterSerialNumber", NOTREQUIRED),
    ("UOM", MANDATORY),
    ("IntervalLength", MANDATORY),
    ("NextScheduledReadDate", NOTREQUIRED)
]

INTERVAL_RECORD_ID = 300
INTERVAL_LENGTHS = ["30", "15"]
ATTRIBUTES[INTERVAL_RECORD_ID] = [
    ("RecordIndicator", MANDATORY),
    ("IntervalDate", MANDATORY),
    ("IntervalValues", MANDATORY),
    ("QualityMethod", MANDATORY),
    ("ReasonCode", NOTREQUIRED),
    ("ReasonDescription", NOTREQUIRED),
    ("UpdateDateTime", NOTREQUIRED),
    ("MSATSLoadDateTime", REQUIRED)
]

EVENT_RECORD_ID = 400
ATTRIBUTES[EVENT_RECORD_ID] = [
    ("RecordIndicator", MANDATORY),
    ("StartInterval", MANDATORY),
    ("EndInterval", MANDATORY),
    ("QualityMethod", MANDATORY),
    ("ReasonCode", NOTREQUIRED),
    ("ReasonDescription", NOTREQUIRED)
]

B2B_RECORD_ID = 500
ATTRIBUTES[B2B_RECORD_ID] = [
    ("RecordIndicator", MANDATORY),
    ("TransCode", MANDATORY),
    ("RetServiceOrder", REQUIRED),
    ("ReadDateTime", NOTREQUIRED),
    ("IndexRead", NOTREQUIRED)
]

class NMIData(Record):
    """
    Represenents a NMI Data details record
    in the NEM-12 file.
    """
    RECORD_ID = NMI_RECORD_ID
    def __init__(self):
        super().__init__(NMI_RECORD_ID, ATTRIBUTES[NMI_RECORD_ID])

class IntervalData(Record):
    """
    Represents an Interval data record
    in the NEM-12 file
    """
    RECORD_ID = INTERVAL_RECORD_ID
    def __init__(self, interval_type):
        self.intervals = [("IntervalValue%d" % i, MANDATORY)
                     for i in range(1, MINUTES_DAILY // int(interval_type) + 1)]
        attributes = ATTRIBUTES[INTERVAL_RECORD_ID][:2] + \
            self.intervals + ATTRIBUTES[INTERVAL_RECORD_ID][3:]
        super().__init__(INTERVAL_RECORD_ID, attributes)

class IntervalEvent(Record):
    """
    Represents an Interval event record
    in the NEM-12 file
    """
    RECORD_ID = EVENT_RECORD_ID
    def __init__(self):
        super().__init__(EVENT_RECORD_ID, ATTRIBUTES[EVENT_RECORD_ID])

class B2BDetails(Record):
    """
    Represents an B2B details record
    in the NEM-12 file
    """
    RECORD_ID = B2B_RECORD_ID
    def __init__(self):
        super().__init__(B2B_RECORD_ID, ATTRIBUTES[B2B_RECORD_ID])
