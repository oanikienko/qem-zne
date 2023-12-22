# Script: Implementation of the zero-noise extrapolation
# Author: oanikienko
# Date: 05/12/2023

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
from qiskit.tools.visualization import plot_histogram

from qiskit.quantum_info import SparsePauliOp
from qiskit.primitives import Estimator, BackendEstimator

from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit_ibm_runtime import Estimator as IBMQEstimator

from qiskit_aer import AerSimulator
from qiskit_aer.primitives import Estimator as AerEstimator

from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.fake_provider import FakeProviderForBackendV2

# from zne import zne, ZNEStrategy
# from zne.utils.serialization import EstimatorResultEncoder
# from zne.noise_amplification import LocalFoldingAmplifier, GlobalFoldingAmplifier
# from zne.extrapolation import PolynomialExtrapolator


## === Functions === ##

def get_experiments_configfile(argv):
    if len(argv) < 2:
        print("Error: An experiments configuration file is required.")
        sys.exit()
    elif len(argv) > 2:
        print("Error: Only 1 experiments configuration file is accepted.")
        sys.exit()
    
    return argv[1]

#TODO simplify this function with intermediate functions
#TODO add the exception/errors management
def set_up_parameters(ibm_cloud_service, ibm_quantum_service, experiments_configuration):

    common_parameters = dict()
    providers_parameters = dict()
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

    # Defining the observable 
    if len(experiments_configuration["observable"]) == 1:
        common_parameters["observable"] = SparsePauliOp(experiments_configuration["observable"]*common_parameters["nb_qubits"])
    elif len(experiments_configuration["observable"]) == common_parameters["nb_qubits"]:
        common_parameters["observable"] = SparsePauliOp(experiments_configuration["observable"])
    #TODO #est-ce la bonne erreur quand l'argument de SparsePauliOp est incorrect ?
    # else:
    #     raise QiskitError 

    # Defining the noise factors
    common_parameters["noise_factors"] = experiments_configuration["noise_factors"]

    # Defining the providers and their backends
    for i in range(len(experiments_configuration["providers"])):
        provider_name = experiments_configuration["providers"][i]["name"]
        providers_parameters[provider_name] = dict()

        # Provider for these experiments
        if provider_name == "fake_provider":
            provider = FakeProviderForBackendV2()
        # elif provider_name == "ibm_quantum_provider":
        #     provider = ibm_quantum_service
        # elif provider_name == "ibm_cloud_provider":
        #     provider = ibm_cloud_service

        # Backends for this provider
        backends = providers.get_backends(provider, experiments_configuration["providers"][i]["backends"])
        providers_parameters[provider_name]["provider_object"] = provider
        providers_parameters[provider_name]["backends_objects"] = backends

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

        # Number of shots for this experiment
        experiment["nb_shots"] = experiments_configuration["experiments"][i]["nb_shots"]

        # Extrapolation for this experiment
        experiment["extrapolations"] = []
        for j in range(len(experiments_configuration["experiments"][i]["extrapolations"])):
            current_extrapolation = dict()
            if experiments_configuration["experiments"][i]["extrapolations"][j]["type"] == "polynomial":
                current_extrapolation["type"] = "polynomial"
                current_extrapolation["function"] = polynomial_extrapolation
                
                current_extrapolation["parameters"] = dict()
                current_extrapolation["parameters"]["degrees"] = experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["degrees"]

                if experiments_configuration["experiments"][i]["extrapolations"][j]["parameters"]["p0"] == "None":
                    current_extrapolation["parameters"]["p0"] = None
                #TODO add the part where p0 is defined and generate a Numpy Array with the initial values given under a list (conversion into Numpy Array easier)
                # else: # p0 size: polynomial_degree + 1

            elif experiments_configuration["experiments"][i]["extrapolations"][j]["type"] == "richardson":
                current_extrapolation["type"] = "richardson"

            elif experiments_configuration["experiments"][i]["extrapolations"][j]["type"] == "exponential":
                current_extrapolation["type"] = "exponential"

            elif experiments_configuration["experiments"][i]["extrapolations"][j]["type"] == "exponential-richardson":
                current_extrapolation["type"] = "exponential-richardson"

            experiment["extrapolations"].append(current_extrapolation)

        experiments_parameters.append(experiment)

    return common_parameters, providers_parameters, experiments_parameters


def select_service(provider_name, ibm_cloud_service, ibm_quantum_service):
    
    service = ibm_cloud_service # Default service

    if provider_name == "ibm_quantum_provider":
        service = ibm_quantum_service

    return service


def filename_from_path(file_path):
    return Path(file_path).stem


def define_experiments_datafile(experiments_configfile):

    experiments_filename = filename_from_path(experiments_configfile)

    return f"./data/{experiments_filename}_results.yaml"


def save_common_parameters(common_parameters, results):
    
    results["circuit"] = common_parameters["circuit"].__name__
    results["nb_qubits"] = common_parameters["nb_qubits"]
    results["observable"] = [observable.to_label() for observable in common_parameters["observable"].paulis]


def initialize_experiments_results(results):

    results["experiments_results"] = []


def extrapolate(fault_rates, ideal_estimations, noisy_estimations, experiment):

    extrapolations_results = []
    
    fault_rates_values = np.array(list(fault_rates.values()))

    ideal_expectation_values = np.array(list(ideal_estimations.values()))[:,0]
    ideal_std_deviations = np.sqrt(np.array(list(ideal_estimations.values()))[:,1])

    noisy_expectation_values = np.array(list(noisy_estimations.values()))[:,0]
    noisy_std_deviations = np.sqrt(np.array(list(noisy_estimations.values()))[:,1])

    for i in range(len(experiment["extrapolations"])):
        extrapolation_results = dict()
        if experiment["extrapolations"][i]["type"] == "polynomial":
            extrapolation_results["type"] = "polynomial"
            extrapolation_results["p0"] = experiment["extrapolations"][i]["parameters"]["p0"]
            extrapolation_results["degrees"] = dict()
            for degree in experiment["extrapolations"][i]["parameters"]["degrees"]:
                # print("[DEBUG]")
                # print("\t degree: ", degree)
                # print("\t noisy_expectation_values: ", noisy_expectation_values)
                # print("\t noisy_std_deviations: ", noisy_std_deviations)

                extrapolation_results["degrees"][degree] = dict()

                optimal_coefs, covariance_matrix = experiment["extrapolations"][i]["function"](degree, fault_rates_values, noisy_expectation_values, noisy_std_deviations)
                coefs_variances = np.diag(covariance_matrix)

                extrapolation_results["degrees"][degree]["optimal_coefs"] = [float(optimal_coef) for optimal_coef in optimal_coefs]
                extrapolation_results["degrees"][degree]["coefs_variances"] = [float(variance) for variance in coefs_variances]

        extrapolations_results.append(extrapolation_results)

    # if experiment["extrapolation"]["type"] == "polynomial":
    #     polynomial_degree = experiment["extrapolation"]["parameters"]["degree"]
    #     coefs_variances = np.diag(covariance_matrix)

    #TODO richardson
    # elif experiment["extrapolation"]["type"] == "richardson":
    #TODO exponential
    # elif experiment["extrapolation"]["type"] == "exponential":
    #TODO exponential-richardson
    # elif experiment["extrapolation"]["type"] == "exponential-richardson":

    return extrapolations_results


def save_experiment_data(provider_name, backend, experiment, nb_shots, fault_rates, ideal_estimations, noisy_estimations, extrapolations_results, results):

    experiment_results = dict()

    experiment_results["provider"] = provider_name
    experiment_results["backend"] = backend.name
    experiment_results["nb_shots"] = nb_shots
    experiment_results["boost_method"] = experiment["boost_method"].__name__

    experiment_results["circuit_results"] = []
    for noise_factor in fault_rates.keys():
        circuit_results = dict()

        circuit_results["noise_factor"] = noise_factor
        circuit_results["fault_rate"] = fault_rates[noise_factor]

        circuit_results["ideal_expectation_value"] = ideal_estimations[noise_factor][0]
        circuit_results["ideal_variance"] = ideal_estimations[noise_factor][1]

        circuit_results["noisy_expectation_value"] = noisy_estimations[noise_factor][0]
        circuit_results["noisy_variance"] = noisy_estimations[noise_factor][1]

        experiment_results["circuit_results"].append(circuit_results)

    experiment_results["extrapolations_results"] = extrapolations_results

    results["experiments_results"].append(experiment_results)


    
## === Global parameters === ##

pp = pprint.PrettyPrinter(indent=3, depth=10, sort_dicts=False)

working_directory = os.getcwd()

global_params_configfile = "./parameters/global_parameters.ini"
credentials_configfile = "./credentials.ini"

# experiments_configfile = "./parameters/experiments_test.yaml"
experiments_configfile = get_experiments_configfile(sys.argv)
experiments_datafile = define_experiments_datafile(experiments_configfile)


## === Main program === ##


### == Loading of the configuration files == ###

print(">> Loading configurations...")

global_params = config.load_config(working_directory, global_params_configfile)
credentials = config.load_config(working_directory, credentials_configfile)

experiments_configuration = yaml_io.load_data(working_directory, experiments_configfile)
pp.pprint(experiments_configuration)


if not config.loaded_configurations(global_params, credentials):
    print("Error: at least one configuration is empty. Please check your *.ini files (filepaths, permissions and syntax).")
    sys.exit()

else: 
    ### == Connection to IBM services == ### 
    # print(">> Connecting to IBM Cloud...")
    # ibm_cloud_service = QiskitRuntimeService(
    #                                 channel=credentials["ibm.cloud"]["channel"],
    #                                 token=credentials["ibm.cloud"]["api_key"],
    #                                 instance=credentials["ibm.cloud"]["instance"]
    #                               )
    ibm_cloud_service = None

    print(">> Connecting to IBM Quantum...")
    ibm_quantum_service = QiskitRuntimeService(
                                channel=credentials["ibm.quantum"]["channel"],
                                token=credentials["ibm.quantum"]["api_token"],
                                instance=credentials["ibm.quantum"]["instance"]
                              )


    ### == Setup of the experiments == ### 
    print(">> Setting up experiments...")
    # TODO vérifier les valeurs et si elles correspondent entre elles (num_qubits = quantum_circuit.num_qubits)
    # TODO modifier les valeurs pour récupérer celles du fichier de configuration
    common_parameters, providers_parameters, experiments_parameters = set_up_parameters(ibm_cloud_service, ibm_quantum_service, experiments_configuration)

    pp.pprint(common_parameters)
    pp.pprint(providers_parameters)
    pp.pprint(experiments_parameters)

    # TODO : considérer que ces variables doivent être fixées pour l'ensemble des expériences ou seulement pour certaines ?
    estimator_optimization_level = 0
    estimator_resilience_level = 0


    print(">> Initializing the results for this run...")
    results = dict()

    print(">> Storing common parameters in the results...")
    save_common_parameters(common_parameters, results)



    #### == Setup of the simulators == ### 
    print(">> Initializing simulators...")
    ideal_simulator = ibm_quantum_service.get_backend("ibmq_qasm_simulator") 
    noisy_simulator = ibm_quantum_service.get_backend("ibmq_qasm_simulator")



    #### == Construction of the circuits == ### 
    print(">> Building the initial circuit...")
    initial_circuit = init.build_initial_circuit(common_parameters["nb_qubits"], common_parameters["circuit"])

    # print(initial_circuit)
    # image = initial_circuit.draw('latex')
    # image.save("./initial_circuit.png")



    #### == Execution of the experiments on the backends == ####
    
    print(">> Executing the experiments on the backends...")

    initialize_experiments_results(results)

    for provider_name in providers_parameters.keys():
        print(f"\t>> Current provider: {provider_name}")

        for backend in providers_parameters[provider_name]["backends_objects"]:
            print(f"\t\t>> Currrent backend: {backend.name}")

            for experiment in experiments_parameters:

                pp.pprint(experiment)

                print("\t\t\t>> Current experiment:")
                print(f"\t\t\t\t - boost_method: {experiment['boost_method'].__name__}")
                print(f"\t\t\t\t - nb_shots: {experiment['nb_shots']}")
                print(f"\t\t\t\t - extrapolations:")
                pp.pprint(experiment["extrapolations"])


                print("\t\t\t>> Initializing the variables for the current experiment...")
                folded_circuits = []

                fault_rates = dict()

                ideal_estimations = dict()
                noisy_estimations = dict()


                print("\t\t\t>> Creating the circuits for the current experiment...")
                for noise_factor in common_parameters["noise_factors"][1:]:
                    folded_circuits.append(experiment["boost_method"](initial_circuit, noise_factor))

                # print("\t\t\t>> Displaying circuits with boosted noise...")
                # for i in range(len(folded_circuits)):
                #     print(folded_circuits[i])


                print("\t\t\t>> Computing the fault rate for each circuit...")
                fault_rates[common_parameters["noise_factors"][0]] = providers.calculate_error_rate(initial_circuit, backend, common_parameters["noise_factors"][0])

                for i in range(len(folded_circuits)):
                    fault_rates[common_parameters["noise_factors"][i+1]] = providers.calculate_error_rate(folded_circuits[i], backend, common_parameters["noise_factors"][i+1])

                # print(fault_rates)

                # TODO loop on experiment["nb_shots"] because now it's a list
                for nb_shots in experiment["nb_shots"]:
                    print(f"\t\t\t\t>> nb_shots = {nb_shots}")

                    #### == Estimation of the expectation value on the ideal simulator, without QEM == ### 
                    print("\t\t\t\t>> Selecting service to use...")
                    service = select_service(provider_name, ibm_cloud_service, ibm_quantum_service)

                    print("\t\t\t\t>> Setting up estimators' options...")
                    ideal_options = Options()
                    ideal_options.execution.shots = nb_shots
                    ideal_options.optimization_level = estimator_optimization_level
                    ideal_options.resilience_level = estimator_resilience_level
                    # print("[DEBUG]")
                    # print(ideal_options)


                    noisy_options = Options()
                    noisy_options.execution.shots = nb_shots
                    noisy_options.optimization_level = estimator_optimization_level
                    noisy_options.resilience_level = estimator_resilience_level
                    noisy_options.simulator = {
                            "noise_model": NoiseModel.from_backend(backend),
                            "basis_gates": backend.operation_names,
                            "coupling_map": backend.coupling_map
                    }
                    # print("[DEBUG]")
                    # print(noisy_options)


                    print("\t\t\t\t>> Running experiments on ideal simulator...")
#TODO replace ibmq_qasm_simulator par simulator 
                    with Session(service=service, backend="ibmq_qasm_simulator") as session:
                        ideal_estimator = IBMQEstimator(session = session, options = ideal_options)

                        print(f"\t\t\t\t\t>> Initial circuit - noise_factor = {common_parameters['noise_factors'][0]}")
                        job = ideal_estimator.run(initial_circuit, common_parameters["observable"])
                        # pp.pprint(job.metrics())

                        result = job.result()
                        ideal_estimations[common_parameters["noise_factors"][0]] = [float(result.values[0]), float(result.metadata[0]['variance'])]

                        for i in range(len(folded_circuits)):
                            print(f"\t\t\t\t\t>> Folded circuit - noise_factor = {common_parameters['noise_factors'][i+1]}")
                            job = ideal_estimator.run(folded_circuits[i], common_parameters["observable"])
                            # pp.pprint(job.metrics())

                            result = job.result()
                            ideal_estimations[common_parameters["noise_factors"][i+1]] = [float(result.values[0]), float(result.metadata[0]['variance'])]



                    #### == Performing experiments on the noisy simulator == ### 
                    print("\t\t\t\t>> Running experiments on noisy simulator...")

                    with Session(service=service, backend=noisy_simulator) as session:
                        noisy_estimator = IBMQEstimator(session = session, options = noisy_options)

                        print(f"\t\t\t\t\t>> Initial circuit - noise_factor = {common_parameters['noise_factors'][0]}")
                        job = noisy_estimator.run(circuits = initial_circuit, observables = common_parameters["observable"])
                        # pp.pprint(job.metrics())

                        result = job.result()
                        noisy_estimations[common_parameters["noise_factors"][0]] = [float(result.values[0]), float(result.metadata[0]['variance'])]

                        for i in range(len(folded_circuits)):
                            print(f"\t\t\t\t\t>> Folded circuit - noise_factor = {common_parameters['noise_factors'][i+1]}")
                            job = noisy_estimator.run(folded_circuits[i], common_parameters["observable"])
                            # pp.pprint(job.metrics())

                            result = job.result()
                            noisy_estimations[common_parameters["noise_factors"][i+1]] = [float(result.values[0]), float(result.metadata[0]['variance'])]



                    #### == Performing extrapolation == ###
                    print("\t\t\t\t>> Extrapolating by fitting a function to the data points...")
                    # print("[DEBUG]")
                    # print(common_parameters["noise_factors"])
                    # pp.pprint(ideal_estimations)
                    # pp.pprint(noisy_estimations)

                    extrapolations_results = extrapolate(fault_rates, ideal_estimations, noisy_estimations, experiment)

                    save_experiment_data(provider_name, backend, experiment, nb_shots, fault_rates, ideal_estimations, noisy_estimations, extrapolations_results, results)

#### == Storage of the data == ###
print(">> Saving data...")
pp.pprint(results)
yaml_io.store_data(results, working_directory, experiments_datafile)

