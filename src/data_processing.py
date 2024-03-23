# Script: data_processing.py
# Author: oanikienko
# Date: 10/12/2023

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
        print("Error: An experiments data file and a directory for the images are required.")
        sys.exit()
    elif len(argv) > 3:
        print("Error: Only 1 experiments data file and 1 directory are accepted.")
        sys.exit()
    
    return argv[1], argv[2]


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


def extrapolation_function(extrapolation_type, fault_rates, optimal_coefs):

    fault_rates = np.array(fault_rates)

    y = dict()

    if extrapolation_type == "polynomial extrapolation":
        for degree in optimal_coefs.keys():
            y[degree] = polynomial_from_coefficients(fault_rates, optimal_coefs[degree][0])


    elif extrapolation_type == "exponential extrapolation":
        y = exponential_from_coefficients(fault_rates, optimal_coefs[0])


    return y


def define_figure_name(working_directory, storage_directory, zne_information, experiment, extrapolation_type):

    extrapolation_type = extrapolation_type.replace(" ", "_")

    fig_name = f"{working_directory}/{storage_directory}/{zne_information['implementation']}_{experiment['backend']}_{experiment['boost_method']}_{experiment['nb_shots']}_{extrapolation_type}.png"

    return fig_name


def build_circuits(experiments_data, experiment, results):

    circuits = []

    # Initial circuit
    circuits_functions = init.get_existing_circuits()
    try:
        common_parameters["circuit"] = circuits_functions[experiments_configuration["circuit"]]
    except KeyError:
        print("Error: the circuit {0} does not exist.".format(experiments_configuration["circuit"]))
        sys.exit()

    circuits.append(init.build_initial_circuit(experiments_data["nb_qubits"], circuits_functions[experiments_data["circuit"]]))
    
    # Folded circuits
    boosting_methods = noise_boosting.get_existing_boosting_methods()
    try:
        experiment["boost_method"] = boosting_methods[experiments_configuration["experiments"][i]["boost_method"]]
    except KeyError:
        print("Error: the boosting method {0} does not exist.".format(experiments_configuration["experiments"][i]["boost_method"]))
        sys.exit()

    for noise_factor in results["noise_factors"][1:]:
        circuits.append(boosting_methods[experiment["boost_method"]](circuits[0], noise_factor))

    return circuits


def customZNE_plot_results(zne_information, experiments_data):

    ### == Data processing == ###
    for experiment in experiments_data["experiments_results"]:

        print(f"\t>> Current experiment:")
        print(f"\t\t provider: {experiment['provider']}")
        print(f"\t\t backend: {experiment['backend']}")
        print(f"\t\t nb_shots: {experiment['nb_shots']}")
        print(f"\t\t boost_method: {experiment['boost_method']}")


        print("\t>> Extracting data...")

        results = extract_results(experiment)

        fault_rates = results["fault_rates"]

        ideal_expectation_values = get_values_per_col(results, "ideal_estimations", 0)
        ideal_std_deviations = np.sqrt(get_values_per_col(results, "ideal_estimations", 1))

        noisy_expectation_values = get_values_per_col(results, "noisy_estimations", 0)
        noisy_std_deviations = np.sqrt(get_values_per_col(results, "noisy_estimations", 1))


        extrapolations_results = process_extrapolations_results(zne_information, results)

        for i in range(len(extrapolations_results)):
            extrapolations_results[i]["extrapolation_function"] = extrapolation_function(extrapolations_results[i]['extrapolation_type'],
                                                                                      fault_rates,
                                                                                      extrapolations_results[i]['optimal_coefs'])

        print("\t>> Plotting the data with variances...")

        plt.rcParams["figure.figsize"] = (9,6)

        for i in range(len(extrapolations_results)):

            plt.grid(which='major',axis='both')

            plt.errorbar([0, fault_rates[-1]],[ideal_expectation_values[0], ideal_expectation_values[-1]], [ideal_std_deviations[0], ideal_std_deviations[-1]], linestyle="--", label=f"Ideal", color="#000000")
            plt.errorbar(fault_rates, noisy_expectation_values, noisy_std_deviations, linestyle='None', marker='.', capsize=3, label=f"Estimates", color="#bc5ed8")

            if extrapolations_results[i]["extrapolation_type"] == "polynomial extrapolation":
                plt.gca().set_prop_cycle(None)
                for degree in extrapolations_results[i]["mitigated_values"].keys():
                    plt.scatter(0.0, extrapolations_results[i]["mitigated_values"][degree][0], label=f"$x^{degree}$", marker="x")

                for degree in extrapolations_results[i]["extrapolation_function"].keys():
                    plt.plot(fault_rates, extrapolations_results[i]["extrapolation_function"][degree], linestyle="-")


            elif extrapolations_results[i]["extrapolation_type"] == "exponential extrapolation":
                plt.gca().set_prop_cycle(None)
                plt.scatter(0.0, extrapolations_results[i]["mitigated_values"][0], label="$e^{x}$", marker="x")

                plt.gca().set_prop_cycle(None)
                plt.plot(fault_rates, extrapolations_results[i]["extrapolation_function"], linestyle="-")


            plt.suptitle("Zero-noise extrapolation", x=0.5, y=0.95, va='center', ha='center')
            plt.title(f"{experiment['backend']}, N_shots = {experiment['nb_shots']}, {experiment['boost_method']}, {extrapolations_results[i]['extrapolation_type']}")
            plt.xlabel("Fault rates")
            plt.ylabel(f"Expectation Value ($\langle {experiments_data['observable'][0]} \\rangle$)")
            plt.legend(ncols=1, bbox_to_anchor=(1.04,1), borderaxespad=0)
            plt.tight_layout()


            print("\t>> Saving the figure...")
            extrapolation_type = extrapolations_results[i]['extrapolation_type'].replace(" ", "_")
            fig_name = f"{working_directory}/{storage_directory}/{zne_information['implementation']}_{experiment['backend']}_{experiment['boost_method']}_{experiment['nb_shots']}_{extrapolation_type}.png"

            plt.savefig(fig_name, bbox_inches='tight')
            plt.close()

def qiskitZNE_plot_results(zne_information, experiments_data):

    experiments_results = dict()

    ### == Data processing == ###
    for experiment in experiments_data["experiments_results"]:

        print(f"\t>> Current experiment:")
        print(f"\t\t provider: {experiment['provider']}")
        print(f"\t\t backend: {experiment['backend']}")
        print(f"\t\t nb_shots: {experiment['nb_shots']}")
        print(f"\t\t boost_method: {experiment['boost_method']}")

        if experiments_results.get(experiment['nb_shots']) is None:
            experiments_results[experiment['nb_shots']] = dict()
            experiments_results[experiment['nb_shots']]['backend'] = experiment['backend']
            experiments_results[experiment['nb_shots']]['boost_method'] = experiment['boost_method']
            experiments_results[experiment['nb_shots']]['fault_rates'] = None

            experiments_results[experiment['nb_shots']]['ideal'] = dict()

            experiments_results[experiment['nb_shots']]['noisy'] = dict()

            experiments_results[experiment['nb_shots']]['extrapolation_type'] = "polynomial extrapolation"

            experiments_results[experiment['nb_shots']]['mitigated_values'] = dict()



        print("\t>> Extracting data...")

        results = extract_results(experiment)

        experiments_results[experiment['nb_shots']]['fault_rates'] = results["fault_rates"]

        # Ideal expectation values and variances
        for noise_factor in results["ideal_estimations"].keys():

            if experiments_results[experiment['nb_shots']]['ideal'].get(noise_factor) is None:
                experiments_results[experiment['nb_shots']]['ideal'][noise_factor] = []

            experiments_results[experiment['nb_shots']]['ideal'][noise_factor].append(results["ideal_estimations"][noise_factor])


        # Noisy expectation values and variances
        for noise_factor in results["noisy_estimations"].keys():

            if experiments_results[experiment['nb_shots']]['noisy'].get(noise_factor) is None:
                experiments_results[experiment['nb_shots']]['noisy'][noise_factor] = []

            experiments_results[experiment['nb_shots']]['noisy'][noise_factor].append(results["noisy_estimations"][noise_factor])


        # Extrapolation results

        for degree in results["extrapolations_results"][0]["degrees"].keys():
            experiments_results[experiment['nb_shots']]['mitigated_values'][degree] = results["extrapolations_results"][0]["degrees"][degree]["noisy_expectation_value"]


    for nb_shots in experiments_results.keys():

        fault_rates = experiments_results[nb_shots]['fault_rates']
        mitigated_values = experiments_results[nb_shots]['mitigated_values']

        extrapolation_type = experiments_results[nb_shots]['extrapolation_type']
        
        ideal_expectation_values = dict()
        ideal_std_deviations = dict()

        noisy_expectation_values = dict()
        noisy_std_deviations = dict()

        for degree in mitigated_values.keys():
            ideal_expectation_values[degree] = get_values_per_col(experiments_results[nb_shots], 'ideal', degree-1)[:,0]
            ideal_std_deviations[degree] = get_values_per_col(experiments_results[nb_shots], 'ideal', degree-1)[:,1]

            noisy_expectation_values[degree] = get_values_per_col(experiments_results[nb_shots], 'noisy', degree-1)[:,0]
            noisy_std_deviations[degree] = get_values_per_col(experiments_results[nb_shots], 'noisy', degree-1)[:,1]

        print("\t>> Plotting the data with variances...")

        plt.rcParams["figure.figsize"] = (9,6)

        plt.grid(which='major',axis='both')

        plt.errorbar([0, fault_rates[-1]],[ideal_expectation_values[1][0], ideal_expectation_values[1][-1]], [ideal_std_deviations[1][0], ideal_std_deviations[1][-1]], linestyle="--", label=f"Ideal", color="#000000")

        for degree in mitigated_values.keys():
            plt.errorbar(fault_rates, noisy_expectation_values[degree], noisy_std_deviations[degree], linestyle='None', marker='.', capsize=3, label=f"Estimates $x^{degree}$")

        plt.gca().set_prop_cycle(None)
        for degree in mitigated_values.keys():
            plt.scatter(0.0, mitigated_values[degree], label=f"$x^{degree}$", marker="x")

        plt.suptitle("Zero-noise extrapolation", x=0.5, y=0.95, va='center', ha='center')
        plt.title(f"{experiment['backend']}, N_shots = {nb_shots}, {experiment['boost_method']}, {extrapolation_type}")
        plt.xlabel("Fault rates")
        plt.ylabel(f"Expectation Value ($\langle {experiments_data['observable'][0]} \\rangle$)")
        plt.legend(ncols=1, bbox_to_anchor=(1.04,1), borderaxespad=0)
        plt.tight_layout()


        print("\t>> Saving the figure...")
        extrapolation_type = extrapolation_type.replace(" ", "_")
        fig_name = f"{working_directory}/{storage_directory}/{zne_information['implementation']}_{experiment['backend']}_{experiment['boost_method']}_{nb_shots}_{extrapolation_type}.png"

        plt.savefig(fig_name, bbox_inches='tight')
        plt.close()


    
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


if not config.loaded_configurations(global_params):
    print("Error: at least one configuration is empty. Please check your configuration files in parameters/ directory (filepaths, permissions and syntax).")
    sys.exit()

else: 

    ### == Matplotlib setup == ###
    print(">> Setting up matplotlib...")
    mpl.rcParams["figure.dpi"] = int(global_params["matplotlib"]["figure_dpi"])
    plt.rcParams.update({"text.usetex": bool(global_params["matplotlib"]["text_usetex"]), "font.family": global_params["matplotlib"]["font_family"], "font.size": int(global_params["matplotlib"]["font_size"])})


    plt.style.use(f'{working_directory}/sizes.mplstyle')

    ### == Data loading == ###

    zne_information = extract_common_information(experiments_data)

    print(f">> Implementation: {zne_information['implementation']}")
    print(f">> Circuit: {zne_information['circuit']}")
    print(f">> Number of qubits: {zne_information['nb_qubits']}")
    print(f">> Observables: {zne_information['observable']}")


    if zne_information["implementation"] == "customZNE":
        customZNE_plot_results(zne_information, experiments_data)

    elif zne_information["implementation"] == "qiskitZNE":
        qiskitZNE_plot_results(zne_information, experiments_data)

