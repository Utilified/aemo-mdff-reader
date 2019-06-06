""" Header Class for nem-reader-importer."""
# import statements
from nemstructure.record import Record, MANDATORY

RECORD_ID = 100
ATTRIBUTES = [
    ("RecordIndicator", MANDATORY),
    ("VersionHeader", MANDATORY),
    ("DateTime", MANDATORY),
    ("FromParticipant", MANDATORY),
    ("ToParticipant", MANDATORY)]

class Header(Record):
    """Represents a header in the NEM-12 file."""
    def __init__(self):
        super().__init__(RECORD_ID, ATTRIBUTES)
