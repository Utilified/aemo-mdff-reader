# import statements
from abc import ABC, ABCMeta, abstractmethod
"""
Record Class for nem-reader-importer
"""

class Record(metaclass=ABCMeta):

    self.MANDATORY = "M"
    self.REQUIRED = "R"
    self.NOT_REQUIRED = "N"

    def __init__(self, record_id, attributes):
        assert isinstance(record_id, int) and isinstance(attributes, dict)
        self.record_id = record_id
        # assigns an expectation of attributes
        self._attr_spec = attributes
        self._attr_len = len(attributes.keys())

        pass

    def __len__(self):
        return self._attr_len
    
    @classmethod
    def read(self, line, delimiter=','):
        """
        
        """
        assert isinstance(line, str)
        data = line.split(delimiter)
        
    @classmethod
    def check(self, parameter_list):
        pass

    class RecordError(Exception):
        "Raised when there is a row error."
        pass

    class TooManyValuesError(RecordError):
        "Raised when there is too many values in record"
        pass
    
    class NotEnoughValuesError(RecordError):
        "Raised when there is not enough values in record"
        pass
    class IncorrectValueError(Exception):
        "Raised when a value is incorrect"
        pass

    pass