# Script: 
# Author: oanikienko
# Date: 05/12/2023

## === Libraries === ##

from utils import yaml_io 
from utils import configuration as config
from circuits import initial_circuits as init
from circuits import noise_boosting
from extrapolation.polynomial_extrapolation import polynomial_function

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
import pprint
import os
import ntpath
from PIL import Image
from pathlib import Path


## === Functions === ##



    
## === Global parameters === ##

pp = pprint.PrettyPrinter(indent=3, depth=5, sort_dicts=False)

working_directory = os.getcwd()

global_params_configfile = "./parameters/global_parameters.ini"

experiments_datafile = "./data/experiments_test_results.yaml"


## === Main program === ##

def extract_results(experiment):

    results = dict()

    results["noise_factors"] = []
    results["fault_rates"] = []
    results["ideal_estimations"] = dict()
    results["noisy_estimations"] = dict()
    results["extrapolation"] = dict()

    for circuit_results in experiment["circuit_results"]:
        results["noise_factors"].append(circuit_results["noise_factor"])
        results["fault_rates"].append(circuit_results["fault_rate"])
        results["ideal_estimations"][circuit_results["noise_factor"]] = [circuit_results["ideal_expectation_value"], circuit_results["ideal_variance"]]
        results["noisy_estimations"][circuit_results["noise_factor"]] = [circuit_results["noisy_expectation_value"], circuit_results["noisy_variance"]]

    results["extrapolation"] = {
            "type": experiment["extrapolation"]["type"],
            "params": experiment["extrapolation"]["parameters"],
            "optimal_coefs": experiment["extrapolation"]["optimal_coefs"],
            "coefs_variances": experiment["extrapolation"]["coefs_variances"],
            "extrapolated_results": [experiment["extrapolation"]["extrapolated_expectation_value"], experiment["extrapolation"]["extrapolated_variance"]]
        }

    return results


#TODO add the exception/errors management
def build_circuits(experiments_data, experiment, results):

    circuits = []

    # Initial circuit
    circuits_functions = init.get_existing_circuits()
    if not hasattr(init, experiments_data["circuit"]):
        print("Error: the circuit {0} does not exist.".format(experiments_data["circuit"]))
        raise KeyError

    circuits.append(init.build_initial_circuit(experiments_data["nb_qubits"], circuits_functions[experiments_data["circuit"]]))
    
    # Folded circuits
    boosting_methods = noise_boosting.get_existing_boosting_methods()
    if not hasattr(noise_boosting, experiment["boost_method"]):
        print("Error: the boosting method {0} does not exist.".format(experiment["boost_method"]))
        raise KeyError

    for noise_factor in results["noise_factors"][1:]:
        circuits.append(boosting_methods[experiment["boost_method"]](circuits[0], noise_factor))

    return circuits



### == Loading of the configuration files == ###

print(">> Loading configurations...")
global_params = config.load_config(working_directory, global_params_configfile)

experiments_data = yaml_io.load_data(working_directory, experiments_datafile)
pp.pprint(experiments_data)


if not config.loaded_configurations(global_params):
    print("Error: at least one configuration is empty. Please check your *.ini files (filepaths, permissions and syntax).")
    sys.exit()

else: 

    ### == Matplotlib setup == ###
    print(">> Setting up matplotlib...")
    mpl.rcParams["figure.dpi"] = int(global_params["matplotlib"]["figure_dpi"])
    plt.rcParams.update({"text.usetex": bool(global_params["matplotlib"]["text_usetex"]), "font.family": global_params["matplotlib"]["font_family"], "font.size": int(global_params["matplotlib"]["font_size"])})



    ### == Data loading == ###
    print(f">> Circuit: {experiments_data['circuit']}")
    print(f">> Number of qubits: {experiments_data['nb_qubits']}")
    print(f">> Observables: {experiments_data['observable']}")


    ### == Data processing == ###
    for experiment in experiments_data["experiments_results"]:
        print(f"\t>> Current experiment:")
        print(f"\t\t provider: {experiment['provider']}")
        print(f"\t\t backend: {experiment['backend']}")
        print(f"\t\t nb_shots: {experiment['nb_shots']}")
        print(f"\t\t boost_method: {experiment['boost_method']}")
        print(f"\t\t extrapolation: {experiment['extrapolation']['type']}")
        print(f"\t\t extrapolation's parameters: {experiment['extrapolation']['parameters']}")

        results = extract_results(experiment)
        pp.pprint(results)


        print("\t>> Displaying the circuits...")
        circuits = build_circuits(experiments_data, experiment, results)
        for circuit in circuits:
            print(circuit)
            #TODO Save the circuit as a PNG image


        print("\t>> Plotting the data with variances...")

        # plt.rcParams["figure.figsize"] = (5,3.5)
        plt.grid(which='major',axis='both')

        noise_factors = results["noise_factors"]

        ideal_expectation_values = np.array(list(results["ideal_estimations"].values()))[:,0]
        ideal_std_deviations = np.sqrt(np.array(list(results["ideal_estimations"].values()))[:,1])

        noisy_expectation_values = np.array(list(results["noisy_estimations"].values()))[:,0]
        noisy_std_deviations = np.sqrt(np.array(list(results["noisy_estimations"].values()))[:,1])

        mitigated_value = results["extrapolation"]["extrapolated_results"][0]

        #TODO add the function used for the extrapolation
        # print(noise_factors)
        # print(results["extrapolation"]["optimal_coefs"])
        # y = polynomial_function(noise_factors[0], results["extrapolation"]["optimal_coefs"])

        plt.errorbar([0, noise_factors[-1]],[ideal_expectation_values[0], ideal_expectation_values[-1]], [ideal_std_deviations[0], ideal_std_deviations[-1]], linestyle="--", label=f"Ideal", color="#000000")
        plt.errorbar(noise_factors, noisy_expectation_values, noisy_std_deviations, linestyle='None', marker='.', capsize=3, label=f"Unmitigated", color="#dc267f")
        plt.scatter(0, mitigated_value, label="Mitigated", marker="x", color="#785ef0")
        # plt.plot(noise_factors, y, label="Extrapolation", linestyle="-", color="red")
        plt.title(f"Zero-noise extrapolation\n{experiment['backend']}, N_shots = {experiment['nb_shots']}, {experiment['boost_method']}, {experiment['extrapolation']['type']} extrapolation")
        plt.xlabel("Noise factors")
        plt.ylabel(f"Expectation Value ($\langle {experiments_data['observable']} \\rangle$)")
        # plt.figtext(0.0, 0.5, f"{experiment['backend']}\nN_shots = {experiment['nb_shots']}\n{experiment['boost_method']}\n{experiment['extrapolation']['type']} extrapolation", fontsize=10)
        plt.legend()
        plt.tight_layout(pad=3.0)

        plt.show()

        # plt.errorbar([0, noise_factors[-1]],[ideal_expectation_values[0], ideal_expectation_values[-1]], [ideal_std_deviations[0], ideal_std_deviations[-1]], linestyle="--", label=f"Ideal", color="#000000")
        # plt.scatter(0, mitigated_value, label="Mitigated", marker="x", color="#785ef0")
        # plt.plot(noise_factors, noisy_expectation_values, linestyle='None', marker='.', label=f"Unmitigated", color="#dc267f")
        # plt.title(f"Zero-noise extrapolation")
        # plt.figtext(1.75, 0.0, f"{experiment['backend']}\nN_shots = {experiment['nb_shots']}\n{experiment['boost_method']}\n{experiment['extrapolation']['type']} extrapolation", fontsize=10)
        # plt.xlabel("Noise factors")
        # plt.ylabel(f"Expectation Value ($\langle {experiments_data['observable']} \\rangle$)")
        # plt.legend()
        # plt.show()



