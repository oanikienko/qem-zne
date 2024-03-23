# Script: Building circuits from an experiments configuration file
# Author: oanikienko
# Date: 13/12/2023

## === Libraries === ##

from utils import configuration as config
from circuits import initial_circuits as init
from circuits import noise_boosting
from circuits import providers
from extrapolation.polynomial_extrapolation import polynomial_extrapolation
from utils import yaml_io 

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy
import sys
import pprint
import os
import ntpath
from PIL import Image
from pathlib import Path

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, transpile, execute
from qiskit.visualization import circuit_drawer


## === Functions === ##

def get_parameters(argv):
    if len(argv) < 3:
        print("Error: An experiments configuration file and a directory for the images are required.")
        sys.exit()
    elif len(argv) > 3:
        print("Error: Only 1 experiments configuration file and 1 directory are accepted.")
        sys.exit()
    
    return argv[1], argv[2]

def extract_circuits_parameters(experiments_configuration):

    common_parameters = dict()
    experiments_parameters = []

    # Defining the circuit
    circuits_functions = init.get_existing_circuits()
    try:
        common_parameters["circuit"] = circuits_functions[experiments_configuration["circuit"]]
    except KeyError:
        print("Error: the circuit {0} does not exist.".format(experiments_configuration["circuit"]))
        sys.exit()

    # Defining the number of qubits
    common_parameters["nb_qubits"] = experiments_configuration["nb_qubits"]

    # Defining the noise factors
    common_parameters["noise_factors"] = experiments_configuration["noise_factors"]

    # Defining the list/dictionary for the experiments 
    for i in range(len(experiments_configuration["experiments"])):
        experiment = dict()

        # Boosting method for this experiment
        boosting_methods = noise_boosting.get_existing_boosting_methods()
        try:
            experiment["boost_method"] = boosting_methods[experiments_configuration["experiments"][i]["boost_method"]]
        except KeyError:
            print("Error: the boosting method {0} does not exist.".format(experiments_configuration["experiments"][i]["boost_method"]))
            sys.exit()

        experiments_parameters.append(experiment)

    return common_parameters, experiments_parameters


## === Main program === ##

experiments_configfile, storage_directory = get_parameters(sys.argv)

working_directory = os.getcwd()

experiments_configuration = yaml_io.load_data(working_directory, experiments_configfile)
common_parameters, experiments_parameters = extract_circuits_parameters(experiments_configuration)

if common_parameters["nb_qubits"] == 4:
    nb_gates_before_fold = 18
elif common_parameters["nb_qubits"] == 5:
    nb_gates_before_fold = 24

initial_circuit = init.build_initial_circuit(common_parameters["nb_qubits"], common_parameters["circuit"])
fig = circuit_drawer(initial_circuit, style=f"{working_directory}/mystyle.json", output='mpl', fold=nb_gates_before_fold)
fig.savefig(f"{working_directory}/{storage_directory}/initialCircuit.png")

for experiment in experiments_parameters:
    
    for noise_factor in common_parameters["noise_factors"][1:]:
        folded_circuit = experiment["boost_method"](initial_circuit, noise_factor)
        fig = circuit_drawer(folded_circuit, style=f"{working_directory}/mystyle.json", output='mpl', fold=nb_gates_before_fold)
        fig.savefig(f"{working_directory}/{storage_directory}/foldedCircuit-bm_{experiment['boost_method'].__name__}-nf_{noise_factor}.png")
        


