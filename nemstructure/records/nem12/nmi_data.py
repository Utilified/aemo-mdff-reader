"NMI data details record for nem-reader-imported"
# import statements
from nemstructure.records.record import Record, MANDATORY, NOTREQUIRED
from nemstructure.records.nem12 import interval_data

__author__ = "Cohen Robinson"
RECORD_ID = 200
ATTRIBUTES = {
    "RecordIndicator": MANDATORY,
    "NMI": MANDATORY,
    "NMIConfiguration": MANDATORY,
    "RegisterID": NOTREQUIRED,
    "NMISuffix": MANDATORY,
    "MDMDataStreamIdentifier": MANDATORY,
    "MeterSerialNumber": NOTREQUIRED,
    "UOM": MANDATORY,
    "IntervalLength": MANDATORY,
    "NextScheduledReadDate": NOTREQUIRED
}
ACCEPTED_SUBRECORDS = []

class NMIData(Record):
    """
    Represenents a NMI Data details record
    in the NEM-12 file.
    """
    def __init__(self, parent):
        super().__init__(RECORD_ID, ATTRIBUTES)
        self.subrecords = []
        self.parent = parent

    def read_subrecord(self, line, delimiter=','):
        """
        Reads a subrecord of the NMIData record
        """
        record_id = line.split(delimiter)[0]
