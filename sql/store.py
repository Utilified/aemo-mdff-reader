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
                reader.data.DateTime,
                reader.data.FromParticipant,
                reader.data.ToParticipant]]
        query = QueryBuilder.insert_query(IMPORT_TABLE, data) \
                + "\n" + "@importID := " + QueryBuilder.get_id_query()
        
        # now store nmi
        data = []
        for subrecord in reader.data.subrecords:
            if isinstance(subrecord, list):
                continue
            if subrecord.RecordIndicator == "200":
                data.append([subrecord.NMI, subrecord.NMIConfiguration])
        query += QueryBuilder.insert_query(NMI_TABLE, data)
        print(query)
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
