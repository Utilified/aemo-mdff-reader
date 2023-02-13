"""End Record for the nem-reader-importer"""
# import statements
from .record import Record, MANDATORY

RECORD_ID = 900
ATTRIBUTES = [("RecordIndicator", MANDATORY)]

class EndRecord(Record):
    """
    Represents an end record in
    the NEM-12 file.
    """
    RECORD_ID = RECORD_ID
    def __init__(self):
        super().__init__(RECORD_ID, ATTRIBUTES)
