# Script: mse_computing.py
# Author: oanikienko
# Date: 20/03/2024

## === Libraries === ##

from utils import yaml_io 
from utils import configuration as config
from circuits import initial_circuits as init
from circuits import noise_boosting
from customZNE.extrapolation.polynomial_extrapolation import polynomial_from_coefficients
from customZNE.extrapolation.exponential_extrapolation import exponential_from_coefficients

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
import sys
import pprint
import os
import ntpath
from PIL import Image
from pathlib import Path


## === Functions === ##

def get_parameters(argv):
    if len(argv) < 3:
        print("Error: An experiments data file and a directory for the results are required.")
        sys.exit()
    elif len(argv) > 3:
        print("Error: Only 1 experiments data file and 1 directory are accepted.")
        sys.exit()
    
    return argv[1], argv[2]


def filename_from_path(file_path):
    return Path(file_path).stem


def define_MSE_file(experiments_datafile, working_directory, storage_directory):

    experiments_filename = filename_from_path(experiments_datafile)

    return f"{working_directory}/{storage_directory}/{experiments_filename}_MSEs.yaml"


def extract_common_information(experiments_data):

    zne_information = dict()

    zne_information["circuit"] = experiments_data["circuit"]
    zne_information["nb_qubits"] = experiments_data["nb_qubits"]
    zne_information["observable"] = experiments_data["observable"]
    
    if experiments_data["optimization_level"] == 0 and experiments_data["resilience_level"] == 0:
        zne_information["implementation"] = "customZNE"
    
    elif experiments_data["optimization_level"] == 0 and experiments_data["resilience_level"] == 2:
        zne_information["implementation"] = "qiskitZNE"

    return zne_information


def extract_results(experiment):

    results = dict()

    results["noise_factors"] = []
    results["fault_rates"] = []
    results["ideal_estimations"] = dict()
    results["noisy_estimations"] = dict()

    for circuit_results in experiment["circuit_results"]:
        results["noise_factors"].append(circuit_results["noise_factor"])
        results["fault_rates"].append(circuit_results["fault_rate"])
        results["ideal_estimations"][circuit_results["noise_factor"]] = [circuit_results["ideal_expectation_value"], circuit_results["ideal_variance"]]
        results["noisy_estimations"][circuit_results["noise_factor"]] = [circuit_results["noisy_expectation_value"], circuit_results["noisy_variance"]]

    results["extrapolations_results"] = experiment["extrapolations_results"]

    return results

def get_values_per_col(dictionary, key, column):
    return np.array(list(dictionary[key].values()))[:,column]

def get_values_per_row(dictionary, key, row):
    return np.array(list(dictionary[key].values()))[row,:]


def process_extrapolations_results(zne_information, results):
    mitigated_values = dict()
    optimal_coefs = dict()

    extrapolations_results = []

    
    if zne_information["implementation"] == "customZNE":
        for i in range(len(results["extrapolations_results"])):
            if results["extrapolations_results"][i]["type"] == "polynomial":
                extrapolation_type = "polynomial extrapolation"
                for degree in results["extrapolations_results"][i]["degrees"].keys():
                    mitigated_values[degree] = [
                                                    results["extrapolations_results"][i]["degrees"][degree]["optimal_coefs"][0],
                                                    results["extrapolations_results"][i]["degrees"][degree]["coefs_variances"][0]
                                               ]
                    optimal_coefs[degree] = [ 
                                                results["extrapolations_results"][i]["degrees"][degree]["optimal_coefs"],
                                                results["extrapolations_results"][i]["degrees"][degree]["coefs_variances"]
                                            ]

                extrapolations_results.append({"extrapolation_type": extrapolation_type,
                                              "mitigated_values": mitigated_values,
                                              "optimal_coefs": optimal_coefs})


            elif results["extrapolations_results"][i]["type"] == "exponential":
                extrapolation_type = "exponential extrapolation"
                mitigated_values = [ exponential_from_coefficients(0, results["extrapolations_results"][i]["optimal_coefs"]) ]
                optimal_coefs = [
                                        results["extrapolations_results"][i]["optimal_coefs"],
                                        results["extrapolations_results"][i]["coefs_variances"]
                                ]

                extrapolations_results.append({"extrapolation_type": extrapolation_type,
                                              "mitigated_values": mitigated_values,
                                              "optimal_coefs": optimal_coefs})


    elif zne_information["implementation"] == "qiskitZNE":
        extrapolation_type = "polynomial extrapolation"

        for degree in results["extrapolations_results"][0]["degrees"].keys():
            mitigated_values[degree] = [results["extrapolations_results"][0]["degrees"][degree]["noisy_expectation_value"]]

        extrapolations_results.append({"extrapolation_type": extrapolation_type,
                                      "mitigated_values": mitigated_values,
                                      "optimal_coefs": optimal_coefs})

    return extrapolations_results


def compute_MSE(expected_value, em_value, em_value_variance, nb_shots):
    return (em_value - expected_value)**2 + em_value_variance/nb_shots

def compute_all_MSE(zne_information, experiments_data):

    MSE_values = dict()
    for experiment in experiments_data["experiments_results"]:

        print(f"\t>> Current experiment:")
        print(f"\t\t provider: {experiment['provider']}")
        print(f"\t\t backend: {experiment['backend']}")
        print(f"\t\t nb_shots: {experiment['nb_shots']}")
        print(f"\t\t boost_method: {experiment['boost_method']}")


        print("\t>> Extracting data...")

        results = extract_results(experiment)
        expected_value = get_values_per_col(results, "ideal_estimations", 0)[0]

        extrapolations_results = process_extrapolations_results(zne_information, results)
        pp.pprint(extrapolations_results)


        if MSE_values.get(experiment['boost_method']) is None:
            MSE_values[experiment['boost_method']] = dict()
            MSE_values[experiment['boost_method']][experiment['nb_shots']] = dict()
            MSE_values[experiment['boost_method']][experiment['nb_shots']]['backend'] = experiment['backend']

        else:
            if MSE_values[experiment['boost_method']].get(experiment['nb_shots']) is None:
                MSE_values[experiment['boost_method']][experiment['nb_shots']] = dict()
                MSE_values[experiment['boost_method']][experiment['nb_shots']]['backend'] = experiment['backend']


        for i in range(len(extrapolations_results)):
            MSE_values[experiment['boost_method']][experiment['nb_shots']]["extrapolation_type"] = extrapolations_results[i]["extrapolation_type"]
            MSE_values[experiment['boost_method']][experiment['nb_shots']]["MSEs"] = dict()

            if extrapolations_results[i]["extrapolation_type"] == "polynomial extrapolation":
                for degree in extrapolations_results[i]["mitigated_values"].keys():
                    em_value = extrapolations_results[i]["mitigated_values"][degree][0]
                    em_variance = extrapolations_results[i]["mitigated_values"][degree][1]
                    MSE_values[experiment['boost_method']][experiment['nb_shots']]["MSEs"][degree] = float(compute_MSE(expected_value, em_value, em_variance, experiment["nb_shots"]))
            
            elif extrapolations_results[i]["extrapolation_type"] == "exponential extrapolation":
                em_value = extrapolations_results[i]["mitigated_values"][0]
                # shift + exp(0)*amplitude = shift + amplitude => variance(em_value at lambda = 0) = variance(shift) + variance(amplitude)
                em_variance = extrapolations_results[i]["optimal_coefs"][0][0] + extrapolations_results[i]["optimal_coefs"][1][1] 
                MSE_values[experiment['boost_method']][experiment['nb_shots']]["MSEs"]["exponential"] = float(compute_MSE(expected_value, em_value, em_variance, experiment["nb_shots"]))

    pp.pprint(MSE_values)

    return MSE_values



## === Global parameters === ##

pp = pprint.PrettyPrinter(indent=3, depth=5, sort_dicts=False)

working_directory = os.getcwd()

global_params_configfile = "./global_parameters.ini"

experiments_datafile, storage_directory = get_parameters(sys.argv)


## === Main program === ##

### == Loading of the configuration files == ###

print(">> Loading configurations...")
global_params = config.load_config(working_directory, global_params_configfile)

experiments_data = yaml_io.load_data(working_directory, experiments_datafile)

MSE_file = define_MSE_file(experiments_datafile, working_directory, storage_directory)


if not config.loaded_configurations(global_params):
    print("Error: at least one configuration is empty. Please check your configuration files in parameters/ directory (filepaths, permissions and syntax).")
    sys.exit()

else: 

    ### == Matplotlib setup == ###
    print(">> Setting up matplotlib...")
    mpl.rcParams["figure.dpi"] = int(global_params["matplotlib"]["figure_dpi"])
    plt.rcParams.update({"text.usetex": bool(global_params["matplotlib"]["text_usetex"]), "font.family": global_params["matplotlib"]["font_family"], "font.size": int(global_params["matplotlib"]["font_size"])})



    ### == Data loading == ###

    zne_information = extract_common_information(experiments_data)

    print(f">> Implementation: {zne_information['implementation']}")
    print(f">> Circuit: {zne_information['circuit']}")
    print(f">> Number of qubits: {zne_information['nb_qubits']}")
    print(f">> Observables: {zne_information['observable']}")

    if zne_information["implementation"] == "customZNE":
        MSE_values = compute_all_MSE(zne_information, experiments_data)

        print("Saving file...")
        print(MSE_file)
        yaml_io.store_data(MSE_values, working_directory, MSE_file)
