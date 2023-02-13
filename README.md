# nem12-reader

The nem12-reader is a tool that reads NEM12 files from the Australian Energy Market Operator (AEMO) and converts them into a more readily available format. This allows for easier analysis and manipulation of energy consumption data for residential, commercial, and industrial customers. 

## Prerequisites

- Python 3.x

## Installation

To install the nem12-reader, clone the repository and install the required packages:

`$ git clone https://github.com/Utilified/nem12-reader.git`
`$ cd nem12-reader`
`$ pip install -r requirements.txt`

## Usage

The nem12-reader can be run from the command line with the following command:

`$ python nem12-reader.py [NEM12 file path] [output file path]`

The `[NEM12 file path]` argument is the path to the NEM12 file that you wish to convert, and the `[output file path]` argument is the desired path for the output file. The output file will be in the CSV format.

## Example

To convert the NEM12 file `sample.csv` to a readable format and save it as `output.csv`, use the following command:

`$ python nem12-reader.py sample.csv output.csv`

## License

This project is licensed. See the [LICENSE](LICENSE) file for details.
