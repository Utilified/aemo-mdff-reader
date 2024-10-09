from nem12_reader import NEMReader
from nem12_reader.nemstructure.nem12 import date
from datetime import datetime as dt
FILENAME = 'test/usageextract_meter_read_elec_nem12_19339_2024-10-09T094550Z.csv'

def test():

    reader = NEMReader()

    reader.read_from_file(FILENAME)

    df = reader.to_dataframe()

    print(df)

    return None

if __name__ == "__main__":

    test()