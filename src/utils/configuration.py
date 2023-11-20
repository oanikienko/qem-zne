# Module: Configuration fonctions
# Author: oanikienko
# Date: 17/11/2023

"""
This module provides the following functions:
 - load_config(filename): load configuration needed for the Qiskit Runtime Service
"""

## == Libraries == ##
import configparser
from pathlib import Path

## == Functions == ##
def load_config(filename):

    config = dict()

    parser = configparser.ConfigParser()

    parser.read(filename)

    for section in parser.sections():
        config[section] = dict()
        for key in parser[section]:
            config[section][key] = parser[section][key]
    
    return config

def print_config(config):
    for section in config:
        print("    [{0}]".format(section))
        for key in config[section]:
            print("         {0} = {1}".format(key, config[section][key]))


## == Tests == ##

if __name__ == "__main__":

    print(">> Defining the .ini file to use...")
    filename = "../credentials.ini"
    path = Path(filename)

    if (path.is_file()):
        print(">> Loading the configuration...")
        config = load_config(filename)

        print(">> Loaded configuration:")
        print_config(config)
    else:
        print(">> Error: file not found.")
