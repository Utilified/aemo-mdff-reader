from reader import Reader
from sql.store import *
from sql.query import *
import configparser
import os
from glob import glob

CONFIG_DIR = 'bin//config.cfg'
SECTION = 'TEST'

def main():
    "Main function for the nem-reader-importer package"

    # first load the config file
    config = configparser.ConfigParser()
    config.read(CONFIG_DIR)
    # read all files and store in memory
    files_read = [file
                 for path, subdir, files in os.walk(config[SECTION]['Directory'])
                 for file in glob(os.path.join(path, '*.csv'))]
    # now begin iterating through read files and store in DB
    storer = Storer(dict(config[SECTION]))
    no_files = 0
    for files in files_read:
        no_files += 1
        print(files)
        storer.load_reader(Reader(files))

if __name__ == "__main__":
    main()
