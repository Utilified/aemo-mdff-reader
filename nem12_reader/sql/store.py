""" Storage for NEM12-13 within SQL Schema as specified. """

# import statements
import pymysql.cursors
from .query import *
import os

# Load queries once session is imported
QUERY_FOLDER = "queries"
QUERIES = {}

class Storer():
    """
    Stores Reader into the DB
    """
    def __init__(self, credentials):
        if credentials is not None:
            self.__connection = self.connect(**credentials)

    @staticmethod
    def connect(host, port, user, password, schema, directory):
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
            host=host,
            user=user,
            password=password,
            db=schema,
            charset='utf8mb4',
            autocommit=True,
            cursorclass=pymysql.cursors.Cursor     # TODO: check if suitable cursor
        )
        return connection

    def load_reader(self, reader):
        """
        loads reader
        """
        print(reader.filename)
        with self.__connection.cursor() as cursor:
            # first store header and filename
            data = [[reader.filename.replace('\\', '/'),
                    reader.data.VersionHeader,
                    f'STR_TO_DATE("{reader.data.DateTime}", "%Y%m%d%k%i%s")',
                    reader.data.FromParticipant,
                    reader.data.ToParticipant]]
            query = QueryBuilder.insert_query(IMPORT_TABLE, data)
            resultset = cursor.execute(query)
            if resultset == 0:
                return None
            cursor.execute("SELECT importID FROM imports WHERE filename LIKE %s", (data[0][0]))
            importID = str(cursor.fetchone()[0])
            print(importID)
            channelID = None
            typeID = None
            intervalID = None
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
                                                f'STR_TO_DATE("{subrecord.NextScheduledReadDate}", "%Y%m%d%k%i%s")',
                                                    channelID,
                                                importID])
                    # add each interval
                    for subsubrecord in subrecord.subrecords:
                        if subsubrecord.RecordIndicator == "300":
                            interval_data = [(key[0].replace("IntervalValue", ""), subsubrecord.__getattr__(key[0]), intervalID) for key in subsubrecord.intervals]
                            data_interval.append([[f'STR_TO_DATE("{subsubrecord.IntervalDate}", "%Y%m%d")',
                                                subsubrecord.QualityMethod,
                                                subsubrecord.ReasonCode,
                                                subsubrecord.ReasonDescription,
                                                f'STR_TO_DATE("{subsubrecord.UpdateDateTime}", "%Y%m%d%k%i%s")',
                                                f'STR_TO_DATE("{subsubrecord.MSATSLoadDateTime}", "%Y%m%d%k%i%s")',
                                                typeID], interval_data])
                        
                    data_intervals.append(data_interval)
            query = QueryBuilder.insert_query(NMI_TABLE, data_nmi)
            resultset = cursor.execute(query)

            for row in range(len(data_channel)):
                query = QueryBuilder.insert_query(CHANNEL_TABLE, [data_channel[row]])
                resultset = cursor.execute(query)
                query = "SELECT channelID FROM `nem`.`channel` WHERE `NMI` = %s AND `NMISuffix` = %s AND `MeterSerialNumber` = %s"
                cursor.execute(query, (data_channel[row][0], data_channel[row][2], data_channel[row][4]))
                channelID = str(cursor.fetchone()[0])
                data_interval_type[row][-2] = channelID
                cursor.execute(QueryBuilder.insert_query(INTERVAL_TYPE_TABLE, [data_interval_type[row]]))
                cursor.execute("""SELECT typeID FROM interval_type WHERE channelID = %s AND importID = %s""", (channelID, importID))
                typeID = str(cursor.fetchone()[0])
                for interval_row in data_intervals[row]:
                    interval_row[0][-1] = typeID
                    query = QueryBuilder.insert_query(INTERVAL_TABLE, [interval_row[0]])
                    cursor.execute(query)
                    cursor.execute('SELECT intervalID FROM `interval` WHERE typeID = %s AND IntervalDate = %s' % (typeID, interval_row[0][0]))
                    intervalID = str(cursor.fetchone()[0])
                    interval_row[1] = [(val[0], val[1], intervalID) for val in interval_row[1]]
                    query = QueryBuilder.insert_query(INTERVAL_DATA_TABLE, list(interval_row[1]))
                    cursor.execute(query) 

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
