# Script: Setup functions for parameters
# Author: oanikienko
# Date: 09/02/2024

## === Libraries === ##

from circuits import initial_circuits as init
from circuits import noise_boosting
from circuits import providers
from customZNE.extrapolation.polynomial_extrapolation import polynomial_extrapolation
from customZNE.extrapolation.exponential_extrapolation import exponential_extrapolation

import sys

from qiskit.exceptions import QiskitError

from qiskit.providers.fake_provider import FakeProviderForBackendV2


## === Functions === ##


def set_up_implementation(experiments_configuration, common_parameters):

    # === customZNE === #
    if experiments_configuration["implementation"] == "customZNE":
        common_parameters["implementation"] = "customZNE"
        common_parameters["optimization_level"] = 0
        common_parameters["resilience_level"] = 0

    # === qiskitZNE === #
    elif experiments_configuration["implementation"] == "qiskitZNE":
        common_parameters["implementation"] = "qiskitZNE"
        common_parameters["optimization_level"] = 0
        common_parameters["resilience_level"] = 2


def set_up_circuit(experiments_configuration, common_parameters):

    circuits_functions = init.get_existing_circuits()
    try:
        common_parameters["circuit"] = circuits_functions[experiments_configuration["circuit"]]

    except KeyError:
        print("Error: the circuit {0} does not exist.".format(experiments_configuration["circuit"]))
        sys.exit()
    
def set_up_num_qubits(experiments_configuration, common_parameters):
    common_parameters["nb_qubits"] = experiments_configuration["nb_qubits"]

def set_up_observable(experiments_configuration, common_parameters):
    common_parameters["observable"] = experiments_configuration["observable"]

def set_up_noise_factors(experiments_configuration, common_parameters):
    common_parameters["noise_factors"] = experiments_configuration["noise_factors"]

def set_up_providers_and_backends(ibm_quantum_service, experiments_configuration, providers_parameters):

    for i in range(len(experiments_configuration["providers"])):
        provider_name = experiments_configuration["providers"][i]["name"]
        providers_parameters[provider_name] = dict()

        # Provider for these experiments
        if provider_name == "fake_provider":
            provider = FakeProviderForBackendV2()
        elif provider_name == "ibm_quantum_provider":
            provider = ibm_quantum_service

        # Run experiments on simulator
        if experiments_configuration["providers"][i].get("run_only_on_simulator") is not None:
            providers_parameters[provider_name]["run_only_on_simulator"] = experiments_configuration["providers"][i]["run_only_on_simulator"]

        # Backends for this provider
        backends = providers.get_backends(provider, experiments_configuration["providers"][i]["backends"])

        # Storage of the provider and its backends
        providers_parameters[provider_name]["provider_object"] = provider
        providers_parameters[provider_name]["backends_objects"] = backends


def set_up_boosting_method(experiments_configuration, i, experiment):

    # === customZNE === #
    if experiments_configuration["implementation"] == "customZNE":
        boosting_methods = noise_boosting.get_existing_boosting_methods()
        try:
            experiment["boost_method"] = boosting_methods[experiments_configuration["experiments"][i]["boost_method"]]
        except KeyError:
            print("Error: the boosting method {0} does not exist.".format(experiments_configuration["experiments"][i]["boost_method"]))
            sys.exit()

    # === qiskitZNE === #
    elif experiments_configuration["implementation"] == "qiskitZNE":
        experiment["boost_method"] = "LocalFoldingAmplifier" # Only LocalFolding available for Qiskit's ZNE


def set_up_current_extrapolation(experiments_configuration, i, j, current_extrapolation):

    # === customZNE === #
    if experiments_configuration["implementation"] == "customZNE":
        # Polynomial extrapolation
        if experiments_configuration["experiments"][i]["extrapolations"][j]["type"] == "polynomial":
            current_extrapolation["type"] = "polynomial"
            current_extrapolation["function"] = polynomial_extrapolation
            
            current_extrapolation["parameters"] = dict()
            current_extrapolation["parameters"]["degrees"] = experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["degrees"]

            if experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["p0"] == "None":
                current_extrapolation["parameters"]["p0"] = None

        # Exponential extrapolation
        elif experiments_configuration["experiments"][i]["extrapolations"][j]["type"] == "exponential":
            current_extrapolation["type"] = "exponential"
            current_extrapolation["function"] = exponential_extrapolation


    # === qiskitZNE === #
    elif experiments_configuration["implementation"] == "qiskitZNE":
        current_extrapolation["type"] = "polynomial"

        if experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["degrees"][0] == 1:
            current_extrapolation["function"] = "LinearExtrapolator"

        elif experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["degrees"][0] == 2:
            current_extrapolation["function"] = "QuadraticExtrapolator"

        elif experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["degrees"][0] == 3:
            current_extrapolation["function"] = "CubicExtrapolator"

        elif experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["degrees"][0] == 4:
            current_extrapolation["function"] = "QuarticExtrapolator"

        current_extrapolation["parameters"] = dict()
        current_extrapolation["parameters"]["degrees"] = experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["degrees"]


def set_up_experiments(experiments_configuration, experiments_parameters):

    for i in range(len(experiments_configuration["experiments"])):
        experiment = dict()

        # Boosting method for this experiment
        set_up_boosting_method(experiments_configuration, i, experiment)

        # Number of shots for this experiment
        experiment["nb_shots"] = experiments_configuration["experiments"][i]["nb_shots"]

        # Extrapolation for this experiment
        experiment["extrapolations"] = []
        for j in range(len(experiments_configuration["experiments"][i]["extrapolations"])):
            current_extrapolation = dict()
            set_up_current_extrapolation(experiments_configuration, i, j, current_extrapolation)
            experiment["extrapolations"].append(current_extrapolation)

        experiments_parameters.append(experiment)
