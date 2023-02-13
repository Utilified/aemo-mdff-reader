""" Contains classes and functions used for building queries in SQL """
# import statements

IMPORT_TABLE = 'imports'
NMI_TABLE = 'nmi'
CHANNEL_TABLE = 'channel'
INTERVAL_TYPE_TABLE = 'interval_type'
INTERVAL_TABLE = 'interval'
INTERVAL_DATA_TABLE = 'interval_data'
INTERVAL_EVENT_TABLE = 'interval_event'
INTERVAL_B2B_TABLE = 'interval_b2b'
ACCUMULATION_DATA_TABLE = 'accumulation_data'
ACCUMULATION_B2B_TABLE = 'accumulation_b2b'

COLUMNS = {
    IMPORT_TABLE: [
        'filename',
        'VersionHeader',
        'DateTime',
        'FromParticipant',
        'ToParticipant'
    ],
    NMI_TABLE: [
        'NMI',
        'NMIConfiguration'
    ],
    CHANNEL_TABLE: [
        'NMI',
        'RegisterID',
        'NMISuffix',
        'MDMDataStreamIdentifier',
        'MeterSerialNumber'
    ],
    INTERVAL_TYPE_TABLE: [
        'UOM',
        'IntervalLength',
        'NextScheduledReadDate',
        'channelID',
        'importID'
    ],
    INTERVAL_TABLE: [
        'IntervalDate',
        'QualityMethod',
        'ReasonCode',
        'ReasonDescription',
        'UpdateDateTime',
        'MSATSLoadDateTime',
        'typeID'
    ],
    INTERVAL_DATA_TABLE: [
        'valueID',
        'value',
        'intervalID'
    ],
    INTERVAL_EVENT_TABLE: [
        'StartInterval',
        'EndInterval',
        'QualityMethod',
        'ReasonCode',
        'ReasonDescription',
        'intervalID'
    ],
    INTERVAL_B2B_TABLE: [
        'TransCode',
        'RetServiceOrder',
        'ReadDateTime',
        'IndexRead',
        'eventID'
    ],
    ACCUMULATION_DATA_TABLE: [],
    ACCUMULATION_B2B_TABLE: []
}

class QueryBuilder():
    """
    Builds a query from given information.
    """
    COLUMN_GEN = 'NULLIF("%s", "")'
    NUM_WRAPPER = 'CAST(%s AS %s)'
    DECIMAL_TYPE_1 = 'DECIMAL(18, 3)'
    DECIMAL_TYPE_2 = 'DECIMAL(22, 5)'
    INT_TYPE = 'INT'
    INSERT_QUERY = '''INSERT INTO %s
                      (%s)
                   '''
    VALUES_QUERY = '''VALUES (%s)'''

    @staticmethod
    def insert_query(table, data):
        """
        Insert query builder
        """
        query = "INSERT IGNORE INTO `%s`\n" % table
        query += "(" + ','.join(['`' + item + '`' for item in COLUMNS[table]]) + ")" + '\n'
        query += "VALUES "
        for instance in data:
            list_value = [(QueryBuilder.COLUMN_GEN % value if '@' not in value and 'STR' not in value else value) for value in instance ]
            query += "("
            for value in list_value:
                query += value + ', '
            query = query[:-2] + "),\n"
        query = query[:-2] + ";"
        return query

    @staticmethod
    def get_id_query():
        """
        Most recent ID retriever
        """
        query = "LAST_INSERT_ID();"

        return query
