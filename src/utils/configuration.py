# Module: Configuration fonctions
# Author: oanikienko
# Date: 17/11/2023

"""
This module provides the following functions:
 - load_config(filename): load configuration needed for the Qiskit Runtime Service
"""

## == Libraries == ##
import configparser

## == Functions == ##
def load_config(filename):

    config = dict()

    parser = configparser.ConfigParser()

    parser.read(filename)

    for section in parser.sections():
        for key in parser[section]:
            config[key] = parser[section][key]
    
    return config

def print_config(config):
    for key in config:
        print("\t{0} = {1}".format(key, config[key]))


## == Tests == ##

if __name__ == "__main__":

    print(">> Defining the .ini file to use...")
    filename = "../config.ini"

    print(">> Loading the configuration...")
    config = load_config(filename)

    print(">> Loaded configuration:")
    print_config(config)
