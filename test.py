from nem12_reader import NEMReader

FILENAME = 'test.csv'

def test():

    reader = NEMReader()

    reader.read_from_file(FILENAME)

    df = reader.to_dataframe()

    print(df)

    return None

if __name__ == "__main__":

    test()