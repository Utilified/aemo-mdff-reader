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
    files_read = [Reader(os.path.join(config[SECTION]['Directory'], filename)) 
                  for filename in os.listdir(config[SECTION]['Directory'])]
    # now begin iterating through read files and store in DB
    storer = Storer(None)
    for reader in files_read:
        storer.load_reader(reader)

    


if __name__ == "__main__":
    main()
    pass