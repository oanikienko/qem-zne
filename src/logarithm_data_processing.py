# Script: logarithm_data_processing.py
# Author: oanikienko
# Date: 16/03/2024

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
from matplotlib.ticker import StrMethodFormatter
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

    fig_name = f"{working_directory}/{storage_directory}/{zne_information['implementation']}_logscale_{experiment['backend']}_{experiment['boost_method']}_{experiment['nb_shots']}_{extrapolation_type}.png"

    return fig_name


def customZNE_plot_results(zne_information, experiments_data):

    data_to_plot = dict()
    ### == Data processing == ###
    for experiment in experiments_data["experiments_results"]:

        print(f"\t>> Current experiment:")
        print(f"\t\t provider: {experiment['provider']}")
        print(f"\t\t backend: {experiment['backend']}")
        print(f"\t\t nb_shots: {experiment['nb_shots']}")
        print(f"\t\t boost_method: {experiment['boost_method']}")


        print("\t>> Extracting data...")

        if data_to_plot.get(experiment['boost_method']) is None:
            data_to_plot[experiment['boost_method']] = dict()

        if data_to_plot[experiment['boost_method']].get(experiment['nb_shots']) is None:
            data_to_plot[experiment['boost_method']][experiment['nb_shots']] = dict()

        results = extract_results(experiment)

        extrapolations_results = process_extrapolations_results(zne_information, results)

        for i in range(len(extrapolations_results)):
            data_to_plot[experiment['boost_method']][experiment["nb_shots"]] = {
                                                "extrapolation_type": extrapolations_results[i]["extrapolation_type"],
                                                "mitigated_values": extrapolations_results[i]["mitigated_values"]
                                            }


    print("\t>> Plotting using logarithm scale...")
    plt.rcParams["figure.figsize"] = (9,6)

    for boost_method in data_to_plot.keys():

        nb_shots = np.array(list(data_to_plot[boost_method].keys()))

        for n in nb_shots:
            
            if data_to_plot[boost_method][n]["extrapolation_type"] == "polynomial extrapolation":
                plt.gca().set_prop_cycle(None)
                for degree in data_to_plot[boost_method][n]["mitigated_values"].keys():
                    plt.scatter(n, data_to_plot[boost_method][n]["mitigated_values"][degree][0], label=f"$x^{degree}$", marker="x")

            elif data_to_plot[boost_method][n]["extrapolation_type"] == "exponential extrapolation":
                plt.gca().set_prop_cycle(None)
                plt.scatter(n, data_to_plot[boost_method][n]["mitigated_values"][0], label="$e^{x}$", marker="x")

        extrapolation_type = extrapolations_results[i]["extrapolation_type"]
        plt.suptitle("Zero-noise extrapolation", x=0.5, y=0.95, va='center', ha='center')
        plt.title(f"{experiment['backend']}, {boost_method}, {extrapolation_type}")
        plt.xlabel("Number of shots")
        plt.ylabel(f"Expectation Value ($\langle {experiments_data['observable'][0]} \\rangle$)")
        plt.xscale("log")

        plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.3f}'))
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), ncols=1, bbox_to_anchor=(1.17,1), borderaxespad=0)
        plt.tight_layout()


        print("\t>> Saving the figure...")
        extrapolation_type = extrapolation_type.replace(" ", "_")
        fig_name = f"{working_directory}/{storage_directory}/{zne_information['implementation']}_logscale_{experiment['backend']}_{boost_method}_{extrapolation_type}.png"

        plt.savefig(fig_name, bbox_inches='tight')
        plt.close()




def qiskitZNE_plot_results(zne_information, experiments_data):

    data_to_plot = dict()
    ### == Data processing == ###
    for experiment in experiments_data["experiments_results"]:

        print(f"\t>> Current experiment:")
        print(f"\t\t provider: {experiment['provider']}")
        print(f"\t\t backend: {experiment['backend']}")
        print(f"\t\t nb_shots: {experiment['nb_shots']}")
        print(f"\t\t boost_method: {experiment['boost_method']}")


        print("\t>> Extracting data...")

        if data_to_plot.get(experiment['boost_method']) is None:
            data_to_plot[experiment['boost_method']] = dict()

        if data_to_plot[experiment['boost_method']].get(experiment['nb_shots']) is None:
            data_to_plot[experiment['boost_method']][experiment['nb_shots']] = dict()
            data_to_plot[experiment['boost_method']][experiment["nb_shots"]]["mitigated_values"] = dict()

        results = extract_results(experiment)

        extrapolations_results = process_extrapolations_results(zne_information, results)

        for i in range(len(extrapolations_results)):
            data_to_plot[experiment['boost_method']][experiment["nb_shots"]]["extrapolation_type"] = extrapolations_results[i]["extrapolation_type"] 

            degree = list(extrapolations_results[i]["mitigated_values"].keys())[0]
            mitigated_value = extrapolations_results[i]["mitigated_values"][degree]
            data_to_plot[experiment['boost_method']][experiment["nb_shots"]]["mitigated_values"][degree] = mitigated_value

    pp.pprint(data_to_plot) 


    print("\t>> Plotting using logarithm scale...")
    plt.rcParams["figure.figsize"] = (9,6)

    for boost_method in data_to_plot.keys():

        nb_shots = np.array(list(data_to_plot[boost_method].keys()))

        for n in nb_shots:
            
            if data_to_plot[boost_method][n]["extrapolation_type"] == "polynomial extrapolation":
                plt.gca().set_prop_cycle(None)
                for degree in data_to_plot[boost_method][n]["mitigated_values"].keys():
                    plt.scatter(n, data_to_plot[boost_method][n]["mitigated_values"][degree][0], label=f"$x^{degree}$", marker="x")

        extrapolation_type = extrapolations_results[i]["extrapolation_type"]
        plt.suptitle("Zero-noise extrapolation", x=0.5, y=0.95, va='center', ha='center')
        plt.title(f"{experiment['backend']}, {experiment['boost_method']}, {extrapolation_type}")
        plt.xlabel("Number of shots")
        plt.ylabel(f"Expectation Value ($\langle {experiments_data['observable'][0]} \\rangle$)")
        plt.xscale("log")

        plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.3f}'))
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), ncols=1, bbox_to_anchor=(1.17,1), borderaxespad=0)
        plt.tight_layout()


        print("\t>> Saving the figure...")
        extrapolation_type = extrapolation_type.replace(" ", "_")
        fig_name = f"{working_directory}/{storage_directory}/{zne_information['implementation']}_logscale_{experiment['backend']}_{boost_method}_{extrapolation_type}.png"

        plt.savefig(fig_name, bbox_inches='tight')
        plt.close()


## === Global parameters === ##

pp = pprint.PrettyPrinter(indent=3, depth=6, sort_dicts=False)

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


