""" Storage for NEM12-13 within SQL Schema as specified. """

# import statements
import pymysql.cursors
import os

# Load queries once session is imported
QUERY_FOLDER = "queries"
QUERIES = {}

class DBCredentials():
    """ Credentials for SQL Database """
    def __init__(self, host, port, schema, username, password):
        self.host = host
        self.port = port
        self.schema = schema
        self.username = username
        self.password = password

class SQLStore():
    """ SQL Store object."""
    def __init__(self, db_credentials):
        # connect to DB
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
        assert isinstance(db_credentials, DBCredentials)
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

    def query_fetch(self, name, args):
        """
        Fetches all results for the query from the server.

        Args:
            name (str)
            args (tuple)
        Returns:
            dict/list.
        """
        with self.__connection.cursor() as cursor:
            query = QUERIES[name]
            cursor.execute(query, args)

            return cursor.fetchall()

    def query_execute(self, name):
        """
        Executes a query from the server

        Args:
            name (str)
        Returns:
            TODO: Fill in
        """
        with self.__connection.cursor() as cursor:
            query = QUERIES[name]
            result = cursor.execute(query)
            return result
