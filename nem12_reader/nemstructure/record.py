""" Record Class for nem-reader-importer """
# import statements
from abc import ABC, abstractmethod

MANDATORY = "M"
REQUIRED = "R"
NOTREQUIRED = "N"


class NEMField(ABC):
    """
    Represents a field within a NEM-12 record.

    key: Label for the field.
    type: Variable type of the field.  
    length: Length of the field.
    required: One of M (Mandatory), R (Required) or N (Not Required).
    """

    def __init__(self, key: str, type: any, length: int,
                 required: str):
        self.__key = key
        self.__type = type
        self.__length = length
        self.__required = required

    def __str__(self) -> str:
        return self.__key

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__key}, \
                 {self.__type}, {self.__required})"

    def __len__(self) -> int:
        return self.__length

    def key(self) -> str:
        """Returns the key assigned to the field."""
        return self.__key

    def type(self) -> any:
        """Returns the type of the field."""
        return self.__type

    @property
    def required(self) -> str:
        """Returns if the field is mandatory, required or not required."""
        return self.__required

    def validate(self, value: any, strict: bool = True) -> bool:
        """Returns if the field is valid, or not."""
        is_type = True
        try:
            # test if value is type
            if value:
                self.type()(value)

            # test if value is greater than length
            if len(value) > len(self):
                raise ValueError()

            # test if value not provided and is mandatory
            if (not len(value)) and (self.required in (MANDATORY)) \
                    and strict:
                raise ValueError()

        except ValueError:
            is_type = False

        return is_type


class Record(ABC):
    """
    Abstract class representing a record within a NEM12 file.
    """
    RECORD_ID = None
    FIELDS = None

    def __init__(self):
        self.__values = None
        self.__children = []
        self.__parent = None
        self.__value_dict = {str(f): None for f in self.FIELDS}

        pass

    def __len__(self): return len(self.FIELDS)

    def __str__(self) -> str: return super().__str__()

    def __repr__(self) -> str: return super().__repr__()

    def __getitem__(self, __item: str) -> any:
        return self.__value_dict[__item]

    def __setitem__(self, __item: str, __value: any) -> any:
        self.__value_dict[__item] = __value
        return None

    @property
    def fields(self) -> list: return self.FIELDS

    @property
    def id(self) -> int: return self.RECORD_ID

    @property
    def values(self) -> list: return self.__values

    @property
    def children(self) -> list: return self.__children

    @property
    def parent(self) -> 'Record': return self.__parent

    def set_parent(self, node: 'Record') -> None:
        """Sets the parent of the current record to the record given."""
        self.__parent = node
        return None

    def add_child(self, child: 'Record') -> None:
        """Adds a child record to the current record."""
        self.__children.append(child)
        child.set_parent(self)
        return None

    def validate(self, row: list) -> bool:
        """
        Validates the provided row using the individual 
        field validations, the length of the row and the record id.

        If validation passes, then no exceptions are raised.
        """
        # check number of values
        if len(row) != len(self):
            raise IncorrectLengthError()

        # check individual validations
        for k, v in zip(self.fields, row):
            if not k.validate(v):
                raise InvalidFieldError()

        # check first record matches
        if self.id != int(row[0]):
            raise IncorrectRecordIDError()

        return None

    def load(self, row: list) -> None:
        """
        Loads the row (list) into the Record. 

        Before loading, the field is validated.
        """
        self.validate(row)

        self.__values = row

        for k, v in zip(self.fields, self.__values):
            if v:
                self[str(k)] = k.type()(v)

        return None


class RecordError(Exception):
    "Raised when there is a row error."


class IncorrectLengthError(RecordError):
    "Raised when a value is incorrect/"


class InvalidFieldError(RecordError):
    """Raised when a field is invalid."""


class IncorrectRecordIDError(RecordError):
    """Raised when a field is invalid."""
