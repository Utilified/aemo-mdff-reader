""" Storage for NEM12-13 within SQL Schema as specified. """

# import statements
import pymysql.cursors
from sql.query import *
import os

# Load queries once session is imported
QUERY_FOLDER = "queries"
QUERIES = {}

class Storer():
    """
    Stores Reader into the DB
    """
    def __init__(self, db_credentials):
        if db_credentials is not None:
            self.__connection = self.connect(db_credentials)

    @staticmethod
    def connect(db_credentials):
        """
        Connects to a MySQL database with the
        given credentials.

        Args:
            db_credentials (DBCredentials): The credentials
                of the DB to connect to
        Returns:
            pymysql.connect. A connection to the DB
        """
        #assert isinstance(db_credentials, DBCredentials)
        # connect to server
        connection = pymysql.connect(
            host=db_credentials.host,
            user=db_credentials.user,
            password=db_credentials.password,
            db=db_credentials.schema,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor     # TODO: check if suitable cursor
        )
        return connection

    def load_reader(self, reader):
        """
        loads reader
        """
        # first store header and filename
        data = [[reader.filename,
                reader.data.VersionHeader,
                f'STR_TO_DATE("{reader.data.DateTime}", "%Y%m%d%h%i%s")',
                reader.data.FromParticipant,
                reader.data.ToParticipant]]
        query = QueryBuilder.insert_query(IMPORT_TABLE, data) \
                + "\n" + "SET @importID = " + QueryBuilder.get_id_query()
        
        # now store nmi, channels and interval type
        data_nmi = []
        data_channel = []
        data_interval_type = []
        data_intervals = []
        for subrecord in reader.data.subrecords:
            if isinstance(subrecord, list):
                continue
            if subrecord.RecordIndicator == "200":
                data_interval = []
                data_nmi.append([subrecord.NMI, subrecord.NMIConfiguration])
                data_channel.append([subrecord.NMI,
                                     subrecord.RegisterID,
                                     subrecord.NMISuffix,
                                     subrecord.MDMDataStreamIdentifier,
                                     subrecord.MeterSerialNumber])
                data_interval_type.append([subrecord.UOM,
                                            subrecord.IntervalLength,
                                            f'STR_TO_DATE("{subrecord.NextScheduledReadDate}", "%Y%m%d%h%i%s")',
                                            "@channelID",
                                            "@importID"])
                # add each interval
                for subsubrecord in subrecord.subrecords:
                    interval_data = [(key[0].replace("IntervalValue", ""), subsubrecord.__getattr__(key[0]), "@intervalID") for key in subsubrecord.intervals]
                    data_interval.append(([f'STR_TO_DATE("{subsubrecord.IntervalDate}", "%Y%m%d")',
                                          subsubrecord.QualityMethod,
                                          subsubrecord.ReasonCode,
                                          subsubrecord.ReasonDescription,
                                          f'STR_TO_DATE("{subsubrecord.UpdateDateTime}", "%Y%m%d%h%i%s")',
                                          f'STR_TO_DATE("{subsubrecord.MSATSLoadDateTime}", "%Y%m%d%h%i%s")',
                                          "@typeID"], interval_data))
                    
                data_intervals.append(data_interval)
        query += QueryBuilder.insert_query(NMI_TABLE, data_nmi)
        for row in range(len(data_channel)):
            query += "\n" + QueryBuilder.insert_query(CHANNEL_TABLE, [data_channel[row]]) + "\n" + "SET @channelID = " + QueryBuilder.get_id_query() + "\n" + QueryBuilder.insert_query(INTERVAL_TYPE_TABLE, [data_interval_type[row]]) + "\n" + "SET @typeID = " + QueryBuilder.get_id_query()
            for interval_row in data_intervals[row]:
                query += "\n" + QueryBuilder.insert_query(INTERVAL_TABLE, [interval_row[0]]) + "\n" + "SET @intervalID = " + QueryBuilder.get_id_query()
                query += "\n" + QueryBuilder.insert_query(INTERVAL_DATA_TABLE, list(interval_row[1]))
        with open("example.sql", "w") as file:
            file.write(query)
        ''' with self.__connection.cursor() as cursor:
            cursor.execute(query)'''

    def close(self):
        """
        Closes the current connection
        """
        self.__connection.close()

class DBCredentials():
    """ Credentials for SQL Database """
    def __init__(self, host, port, schema, username, password):
        self.host = host
        self.port = port
        self.schema = schema
        self.username = username
        self.password = password
