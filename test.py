from nem12_reader import NEMReader

FILENAME = 'test/ba817cc5-7835-4da5-bbec-1cbe71e1afb0.csv'

def test():

    reader = NEMReader()

    reader.read_from_file(FILENAME)

    df = reader.to_dataframe()

    print(df)

    return None

if __name__ == "__main__":

    test()