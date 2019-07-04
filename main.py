from reader import Reader
from sql.store import *
from sql.query import *
import configparser
import os

CONFIG_DIR = 'bin//config.cfg'
SECTION = 'TEST'

def main():
    "Main function for the nem-reader-importer package"

    # first load the config file
    config = configparser.ConfigParser()
    config.read(CONFIG_DIR)
    # read all files and store in memory
    files_read = [os.path.join(config[SECTION]['Directory'], filename)
                  for filename in os.listdir(config[SECTION]['Directory'])]
    # now begin iterating through read files and store in DB
    db_credentials = None
    storer = Storer(db_credentials)
    for files in files_read:
        storer.load_reader(Reader(files))

if __name__ == "__main__":
    main()
