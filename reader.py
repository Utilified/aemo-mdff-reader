""" Reads a NEM12/NEM13 file into file. """
# import statements
import csv

from nemstructure.header import Header
from nemstructure.end import EndRecord
from nemstructure.nem12 import NMIData, IntervalData
from nemstructure.nem12 import IntervalEvent, B2BDetails
from nemstructure.nem13 import AccummulationData as AccummulationData13
from nemstructure.nem13 import B2BDetails as B2BDetails13

class Reader():
    """
    A reader class for the NEM12/13 file.
    """
    def __init__(self, filename):
        self.__filename = filename
        self.data = self.read(filename)

    @staticmethod
    def read(filename):
        """
        Reads given filename as per AEMO spec.

        Args:
            filename (str): Name of the file
        Returns:

        """
        with open(filename, 'rt', encoding="utf8") as file:
            file_reader = list(csv.reader(file))
            current_header = None
            current_nmi = None
            current_interval = None
            for row_no in range(len(file_reader)):
                row = file_reader[row_no]
                current_row = None
                # TODO: replace with recursive function
                if int(row[0]) == Header.RECORD_ID:
                    current_row = Header()
                    current_row.read(row)
                    current_header = current_row
                elif int(row[0]) == NMIData.RECORD_ID:
                    current_row = NMIData()
                    current_row.read(row)
                    current_nmi = current_row
                    current_header.add_subrecord(current_row)
                elif int(row[0]) == IntervalData.RECORD_ID:
                    current_row = IntervalData(current_nmi.IntervalLength)
                    current_row.read(row)
                    current_interval = current_row
                    current_nmi.add_subrecord(current_row)
                elif int(row[0]) == IntervalEvent.RECORD_ID:
                    current_row = IntervalEvent()
                    current_row.read(row)
                    current_interval.add_subrecord(current_row)
                elif int(row[0]) == B2BDetails.RECORD_ID:
                    current_row = B2BDetails()
                    current_row.read(row)
                    current_nmi.add_subrecord(current_row)
                elif int(row[0]) == AccummulationData13.RECORD_ID:
                    current_row = AccummulationData13()
                    current_row.read(row)
                    current_interval = current_row
                    current_header.add_subrecord(current_row)
                elif int(row[0]) == B2BDetails13.RECORD_ID:
                    current_row = B2BDetails13()
                    current_row.read(row)
                    current_interval.add_subrecord(current_row)
                else:
                    # EOF
                    current_row = EndRecord()
                    current_row.read(row)
                    current_header.add_subrecord(row)
                    break
        return current_header
