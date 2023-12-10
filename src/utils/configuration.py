# Module: Configuration fonctions
# Author: oanikienko
# Date: 17/11/2023

"""
This module provides the following functions:
 - load_config(filename): load configuration needed for the Qiskit Runtime Service
"""

## == Libraries == ##
import configparser
import errno
import os
from pathlib import Path

## == Functions == ##

def is_empty(config):
    return config == dict()

def loaded_configurations(*configs):
    
    for config in enumerate(configs):
        if is_empty(config):
            return False

    return True

def load_config(working_directory, filename):

    config = dict()

    base_path = Path(working_directory)
    file_path = (base_path / filename).resolve()

    if (file_path.exists() and file_path.is_file()):
        parser = configparser.ConfigParser()
        parser.read(file_path)

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

    print(">> Loading the configuration...")
    config = load_config(filename)

    if not is_empty(config):
        print(">> Loaded configuration:")
        print_config(config)
    else:
        print(">> Error: file not found.")
