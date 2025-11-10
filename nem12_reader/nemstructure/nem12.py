"""NMI data details record for nem-reader-imported"""
# import statements
from .record import Record, NEMField, MANDATORY, REQUIRED, NOTREQUIRED
from datetime import datetime
ATTRIBUTES = {}
MINUTES_DAILY = 24 * 60

def date(date_string):
    # List of possible formats
    formats = ['%Y%m%d%H%M%S', '%Y%m%d', '%Y-%m-%d']
    
    # Try each format until one works
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    # If none of the formats match, raise an error or return None
    raise ValueError(f"No valid date format found for {date_string}")

def date_time(date_string):
    # List of possible formats
    formats = ['%Y%m%d%H%M%S', '%Y%m%d', '%Y-%m-%d']
    
    # Try each format until one works
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    # If none of the formats match, raise an error or return None
    raise ValueError(f"No valid date format found for {date_string}")


HEADER_RECORD_ID = 100
ATTRIBUTES[HEADER_RECORD_ID] = [
    NEMField("RecordIndicator", int, 3, MANDATORY),
    NEMField("VersionHeader", str, 5, MANDATORY),
    NEMField("DateTime", date_time, 14, MANDATORY),
    NEMField("FromParticipant", str, 10, NOTREQUIRED),
    NEMField("ToParticipant", str, 10, NOTREQUIRED)]

NMI_RECORD_ID = 200
INTERVAL_LENGTHS = [30, 15, 10, 5, 1]
ATTRIBUTES[NMI_RECORD_ID] = [
    NEMField("RecordIndicator", int, 3, MANDATORY),
    NEMField("NMI", str, 10, MANDATORY),
    NEMField("NMIConfiguration", str, 250, MANDATORY),
    NEMField("RegisterID", str, 10, NOTREQUIRED),
    NEMField("NMISuffix", str, 2, MANDATORY),
    NEMField("MDMDataStreamIdentifier", str, 2, NOTREQUIRED),
    NEMField("MeterSerialNumber", str, 12, NOTREQUIRED),
    NEMField("UOM", str, 5, MANDATORY),
    NEMField("IntervalLength", int, 2, MANDATORY),
    NEMField("NextScheduledReadDate", date, 10, NOTREQUIRED)
]

INTERVAL_RECORD_ID = 300
ATTRIBUTES[INTERVAL_RECORD_ID] = [[
    NEMField("RecordIndicator", int, 3, MANDATORY),
    NEMField("IntervalDate", date, 8, MANDATORY)], 
    lambda x: [
    NEMField("IntervalValue%d" % i, float, 100, MANDATORY) 
    for i in range(1, x)], [
    NEMField("QualityMethod", str, 3, MANDATORY),
    NEMField("ReasonCode", int, 3, NOTREQUIRED),
    NEMField("ReasonDescription", str, 240, NOTREQUIRED),
    NEMField("UpdateDateTime", date_time, 14, NOTREQUIRED),
    NEMField("MSATSLoadDateTime", date_time, 14, REQUIRED)]
]

EVENT_RECORD_ID = 400
ATTRIBUTES[EVENT_RECORD_ID] = [
    NEMField("RecordIndicator", int, 3, MANDATORY),
    NEMField("StartInterval", int, 4, MANDATORY),
    NEMField("EndInterval", int, 4, MANDATORY),
    NEMField("QualityMethod", str, 3, NOTREQUIRED),
    NEMField("ReasonCode", int, 3, NOTREQUIRED),
    NEMField("ReasonDescription", str, 240, NOTREQUIRED)
]

B2B_RECORD_ID = 500
ATTRIBUTES[B2B_RECORD_ID] = [
    NEMField("RecordIndicator", int, 3, MANDATORY),
    NEMField("TransCode", str, 1, MANDATORY),
    NEMField("RetServiceOrder", str, 15, REQUIRED),
    NEMField("ReadDateTime", date_time, 14, NOTREQUIRED),
    NEMField("IndexRead", str, 15, NOTREQUIRED)
]

END_RECORD_ID = 900
ATTRIBUTES[END_RECORD_ID] = [
    NEMField("RecordIndicator", int, 3, MANDATORY),]


class Header(Record):
    """
    Represents a header 
    in the NEM-12 file.
    """
    RECORD_ID = HEADER_RECORD_ID
    FIELDS = ATTRIBUTES[HEADER_RECORD_ID]
    pass

class NMIData(Record):
    """
    Represenents a NMI Data details record
    in the NEM-12 file.
    """
    RECORD_ID = NMI_RECORD_ID
    FIELDS = ATTRIBUTES[NMI_RECORD_ID]
    pass

class IntervalData(Record):
    """
    Represents an Interval data record
    in the NEM-12 file
    """
    RECORD_ID = INTERVAL_RECORD_ID
    FIELDS = None

    def __init__(self, interval_type):
        ints = MINUTES_DAILY // int(interval_type) + 1
        self.intervals = ATTRIBUTES[INTERVAL_RECORD_ID][1](ints)
        attributes = ATTRIBUTES[INTERVAL_RECORD_ID][0] + \
            self.intervals + ATTRIBUTES[INTERVAL_RECORD_ID][2]

        self.FIELDS = attributes
        super().__init__()
    
    pass


class IntervalEvent(Record):
    """
    Represents an Interval event record
    in the NEM-12 file
    """
    RECORD_ID = EVENT_RECORD_ID
    FIELDS = ATTRIBUTES[EVENT_RECORD_ID]
    pass


class B2BDetails(Record):
    """
    Represents an B2B details record
    in the NEM-12 file
    """
    RECORD_ID = B2B_RECORD_ID
    FIELDS = ATTRIBUTES[B2B_RECORD_ID]
    pass


class EndRecord(Record):
    """
    Represents an end record in
    the NEM-12 file.
    """
    RECORD_ID = END_RECORD_ID
    FIELDS = ATTRIBUTES[END_RECORD_ID]


RECORDS = {
    HEADER_RECORD_ID: Header, 
    NMI_RECORD_ID: NMIData, 
    INTERVAL_RECORD_ID: IntervalData,
    EVENT_RECORD_ID: IntervalEvent, 
    B2B_RECORD_ID: B2BDetails, 
    END_RECORD_ID: EndRecord
}