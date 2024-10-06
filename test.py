from nem12_reader import NEMReader

FILENAME = 'test/usageextract_meter_read_elec_nem12_19234_2024-10-06T103313Z.csv'

def test():

    reader = NEMReader()

    reader.read_from_file(FILENAME)

    df = reader.to_dataframe()

    print(df)

    return None

if __name__ == "__main__":

    test()