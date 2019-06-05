""" Record Class for nem-reader-importer """
# import statements

__author__ = "Cohen Robinson"
MANDATORY = "M"
REQUIRED = "R"
NOTREQUIRED = "N"

class Record():
    """
    Represents a record in the NEM-12 file,
    all attributes inherit from this class.
    """
    def __init__(self, record_id, attributes):
        assert isinstance(record_id, int) and isinstance(attributes, list)
        self.record_id = record_id
        # assigns an expectation of attributes
        self.__attr_spec = attributes
        self.__attr_len = len(attributes)
        self.__record_data = None

    def __str__(self):
        return str(self.__record_data)

    def __len__(self):
        return self.__attr_len

    def read(self, line, delimiter=','):
        """
        Reads the line and checks if the data matches the requirements
        for the record.

        Args:
            line (str): The line to read.
        Kwargs:
            delimiter (str): The delimiter to split the line with.
        Returns:
            dict. The 'checked' data::
                AttributeName: Data
        """
        assert isinstance(line, str)
        data = line.split(delimiter)
        self.__record_data = self.check(data)

    def check(self, data):
        """
        Checks if the data matches the requirements for the record.

        Returns a dict of the loaded data, otherwise raises a RecordError.
        """
        transformed_data = {}
        # check if length of data matches expectation
        if len(data) < len(self):
            raise NotEnoughValuesError()
        if len(data) > len(self):
            raise TooManyValuesError()
        # check if field requirements matches each field
        for i in range(len(data)):
            attribute_name = self.__attr_spec[i][0]
            attribute_requirement = self.__attr_spec[i][1]

            if attribute_requirement == MANDATORY & data[i] == "":
                raise IncorrectValueError()

            transformed_data[attribute_name] = data[i]
        return transformed_data

class RecordError(Exception):
    "Raised when there is a row error."

class TooManyValuesError(RecordError):
    "Raised when there is too many values in record"

class NotEnoughValuesError(RecordError):
    "Raised when there is not enough values in record"

class IncorrectValueError(RecordError):
    "Raised when a value is incorrect"
