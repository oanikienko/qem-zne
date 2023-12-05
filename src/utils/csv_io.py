# Module: Functions for loading and storing data (CSV format)
# Author: oanikienko
# Date: 17/11/2023

"""
This module contains the following functions:
 - 
"""

## == Libraries == ##

import numpy as np
import csv
from pathlib import Path

## == Functions == ##

def load_data(filename, separator=';'):
    """
    Load the data stored in a CSV file.

    Parameters
    ----------
    filename : string
        Path to the file
    separator : string
        Separator between values in the CSV file. By default: ';'.

    Returns
    ---------
    fields : list
        List of the fields in the CSV file.
    data : list
        List of the rows in the CSV file.
    """

    fields = []
    data = []
    row = []

    path = Path(__file__).parent / filename

    with open(path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=separator)
        fields = next(csvreader)
        for line in csvreader:
            for i in range(len(line)):
                row.append(float(line[i]))
            data.append(row)
            row = []

    return fields, data


def store_data(fields, data, filename, separator=';'):
    """
    Store the data in a CSV file.

    Parameters
    ----------
    fields : list
        List of the fields in the CSV file.
    data : list
        List of the rows in the CSV file.
    filename : string
        Path to the file
    separator : string
        Separator between values in the CSV file. By default: ';'.
    """

    path = Path(__file__).parent / filename

    for i in range(len(data)):
        data[i] = [str(x) for x in data[i]]

    with open(path, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=separator)
        csvwriter.writerow(fields)
        for i in range(len(data)):
            csvwriter.writerow(data[i])
        

    
## == Tests == ##

if __name__ == "__main__":

    print(">> Defining the .csv file to use...")
    filename = "../../data/test.csv"

    print(">> Creating data to store...")
    fields = ["Expectation value", "Variance"]
    values = [[0.654, 0.572284], [0.546, 0.701884], [0.536, 0.712704]]

    print(">> Before storing data:")
    print(fields)
    print(values)

    store_data(fields, values, filename)

    fields, values = load_data(filename)

    print(">> After loading data:")
    print(fields)
    print(values)

