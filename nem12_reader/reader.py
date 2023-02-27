import pandas as pd
import csv
from .nemstructure import Header, NMIData, IntervalData, Record, RECORDS


INTERVAL_DATA_OUTPUT_HEADERS = [
    'NMI',
    'MeterSerial',
    'Register',
    'Date',
    'Interval',
    'IntervalLength',
    'UOM',
    'IntervalValue',
    'Quality',
    'UpdateDatetime',
]


class NEMReader():
    """
    Reads NEM12 files using the AEMO specification.

    Read more here: https://www.aemo.com.au/-/media/files/electricity/nem/retail_and_metering/metering-procedures/2017/mdff_specification_nem12_nem13_final_v102.pdf
    """
    INTERVAL_DATA_OUTPUT_HEADERS = INTERVAL_DATA_OUTPUT_HEADERS

    def __init__(self) -> None:
        self.__tree = None
        self.__source_filename = None
        pass

    def get_parent(self, record_id: int, parent: Record) -> None:
        """
        Returns the parent of the record, given a proposed record_id and
        the current node.
        """
        if record_id == None:
            return None
        elif record_id <= parent.id:
            return self.get_parent(record_id, parent.parent)

        return parent

    def build_tree(self, array: list, root_node: Record) -> None:
        """
        Builds the tree, using the first value of the array and
        the current node.
        """
        record_id = int(array[0][0])
        record_class = RECORDS[record_id]
        new_node = None

        parent_node = self.get_parent(record_id, root_node)

        if record_id == IntervalData.RECORD_ID:
            new_node = record_class(parent_node['IntervalLength'])
        else:
            new_node = record_class()

        new_node.load(array[0])

        parent_node.add_child(new_node)

        return new_node

    def read_from_array(self, array: list) -> None:
        """
        Reads the NEM12 file from the array given.
        """
        nem_tree = Header()
        nem_tree.load(array[0])
        array = array[1:]
        parent_node = nem_tree

        while len(array):
            parent_node = self.build_tree(array, parent_node)
            array = array[1:]

        self.__tree = nem_tree
        pass

    def read_from_file(self, filename: str) -> None:
        """
        Reads the NEM12 file from the filename given.

        Assumes the filename is provided in CSV format.
        """
        self.__source_filename = filename
        rows = []
        with open(self.__source_filename, 'r') as in_file:
            in_rows = csv.reader(in_file)
            for row in in_rows:
                rows.append(row)
        self.read_from_array(rows)
        pass

    @staticmethod
    def extract_data_from_tree(node: Record, header: Header = None, nmi_data: NMIData = None):
        """
        Extracts interval data from the tree node given.

        Currently B2B and IntervalEvent details are not used.
        """
        array = []
        if isinstance(node, (Header, NMIData)):
            if isinstance(node, (Header)):
                header = node
            else:
                nmi_data = node

            for child in node.children:
                array += NEMReader.extract_data_from_tree(
                    child, header, nmi_data)

        elif isinstance(node, IntervalData):
            for i in range(1, len(node.intervals)+1):
                array.append([
                    nmi_data['NMI'],
                    nmi_data['MeterSerialNumber'],
                    nmi_data['RegisterID'],
                    node['IntervalDate'],
                    i,
                    nmi_data['IntervalLength'],
                    nmi_data['UOM'],
                    node[f'IntervalValue{i}'],
                    node['QualityMethod'],
                    node['UpdateDateTime']
                ])

        return array

    def to_dataframe(self) -> pd.DataFrame:
        """Exports the currently loaded NEM12 tree to a dataframe."""
        array = None
        df = None
        # gather data from tree (Header, NMIData, IntervalData)
        array = self.extract_data_from_tree(self.__tree)

        # load array into pandas dataframe
        df = pd.DataFrame(array, columns=INTERVAL_DATA_OUTPUT_HEADERS)

        return df

    def to_csv(self, filename) -> None:
        """Exports the currently loaded NEM12 tree to file."""
        self.to_dataframe().to_csv(filename)
