# Script: Implementation of the zero-noise extrapolation
#         using local folding to boost the noise
# Author: oanikienko
# Date: 30/11/2O23

## == Libraries == ##

from utils import configuration
from circuits import initial_circuits as init
from circuits import folding
from circuits import providers
from extrapolation.polynomial_extrapolation import polynomial_extrapolation

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy
from pathlib import Path
import sys
import pprint

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, transpile, execute
from qiskit.tools.visualization import plot_histogram

from qiskit.quantum_info import SparsePauliOp
from qiskit.primitives import Estimator, BackendEstimator

from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit_ibm_runtime import Estimator as IBMQEstimator

from qiskit_aer import AerSimulator
from qiskit_aer.primitives import Estimator as AerEstimator

from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.fake_provider import FakeNairobiV2


## === Global parameters === ##

credentials_file = "../credentials.ini"
global_params_file = "../parameters/global_parameters.ini"

#TODO csv_io.py gère-t-il les chemins relatifs pour les fichiers ?
# TODO réfléchir à comment structurer les données (global/local/partial foldings, etc.)
circuits_data_file = "../data/circuits/TEST.csv"
measurements_data_file = "../data/measurements/TEST.csv"
extrapolations_data_file = "../data/extrapolations/TEST.csv"

## === Functions === ##

# TODO une fonction pour charger toutes les configurations ?
# TODO une fonction qui initialise le pointeur chosen_U pour init.build_initial_circuit à partir de la valeur stockée dans le .ini => TODO ajouter des circuits par défaut si pas défini dans *.ini


## === Main program === ##


### == Loading of the configuration files == ###
print(">> Loading configurations...")

global_params = configuration.load_config(global_params_file)
credentials = configuration.load_config(credentials_file)
# experiments_4qubits
# experiments_5qubits


if not configuration.loaded_configurations(global_params, credentials):
    print("Error: at least one configuration is empty. Please check your *.ini files (filepaths, permissions, syntax).")
    sys.exit()

else: 

    ### == Matplotlib setup == ###
    print(">> Setting up matplotlib...")
    mpl.rcParams["figure.dpi"] = int(global_params["matplotlib"]["figure_dpi"])
    plt.rcParams.update({"text.usetex": bool(global_params["matplotlib"]["text_usetex"]), "font.family": global_params["matplotlib"]["font_family"]})



    ### == Connection to IBM Cloud == ### 
    print(">> Connecting to IBM Cloud...")
    # configuration.print_config(credentials)
    service = QiskitRuntimeService(
                                    channel=credentials["ibmq.cloud"]["channel"],
                                    token=credentials["ibmq.cloud"]["api_key"],
                                    instance=credentials["ibmq.cloud"]["instance"]
                                  )



    ### == Setup of the experiments == ### 
    print(">> Setting up experiments...")
    # TODO print experiments?
    # TODO modifier les valeurs pour récupérer celles du fichier de configuration
    pp = pprint.PrettyPrinter(indent=3, depth=5, sort_dicts=False)
    nb_qubits = 4
    nb_shots = 10000 #TODO only for tests: 100
    estimator_optimization_level = 0
    estimator_resilience_level = 0
    observable = SparsePauliOp("Z" * nb_qubits) # print(f"\tObservable: {observable.paulis}")
    fake_backend = FakeNairobiV2()
    fake_backend_noise_model = NoiseModel.from_backend(fake_backend)
    polynomial_degree = 2
    
    noise_factors = [1, 3, 5, 7]# TODO modifier noise_factors pour récupérer la valeur stockée dans les fichiers .ini

    folded_circuits = []

    fault_rates = dict()
    ideal_estimations_results = []
    noisy_estimations_results = []



    ### == Setup of the simulators == ### 
    print(">> Setting up simulators...")
    ideal_simulator = service.get_backend("ibmq_qasm_simulator") 

    noisy_simulator = service.get_backend("ibmq_qasm_simulator")

    noisy_options = Options()
    noisy_options.execution.shots = nb_shots
    noisy_options.optimization_level = estimator_optimization_level
    noisy_options.resilience_level = estimator_resilience_level
    noisy_options.simulator = {
            "noise_model": fake_backend_noise_model,
            "basis_gates": fake_backend.operation_names,
            "coupling_map": fake_backend.coupling_map
    }


    ### == Setup of the estimators == ### 
    print(">> Setting up estimators...")
    ideal_estimator = Estimator()
    ideal_estimator.set_options(shots=nb_shots)



    ### == Setup of the estimators == ### 
    print(">> Setting up extrapolations...")
    #TODO

    

    ### == Construction of the circuits == ### 
    print(">> Building circuits...")
    initial_circuit = init.build_initial_circuit(nb_qubits, init.U_4qubits) #TODO ajouter choix de U dans le .ini avec vérification de l'existence de la fonction

    for noise_factor in noise_factors[1:]:
        folded_circuits.append(folding.local_folding(initial_circuit, nb_qubits, noise_factor))

    print(">> Computing the fault rate for each circuit...")
    fault_rates[noise_factors[0]] = providers.calculate_error_rate(initial_circuit, fake_backend, noise_factors[0])

    for i in range(len(folded_circuits)):
        fault_rates[noise_factors[i+1]] = providers.calculate_error_rate(folded_circuits[i], fake_backend, noise_factors[i+1])

    # print(fault_rates)



    ### == Display of the circuits == ### 
    print(">> Displaying circuits...")
    print(initial_circuit)
    for i in range(len(folded_circuits)):
        print(folded_circuits[i])

    # fig = initial_circuit.draw('mpl')
    # fig.suptitle("Initial circuit")
    # plt.show()



    ### == Estimation of the expectation value on the ideal simulator, without QEM == ### 
    print(">> Running experiments on ideal simulator...")

    print(f">>>> Initial circuit - noise_factor = {noise_factors[0]}")
    job = ideal_estimator.run(initial_circuit, observable)
    result = job.result()
    ideal_estimations_results.append([result.values[0], result.metadata[0]['variance']])

    for i in range(len(folded_circuits)):
        print(f">>>> Folded circuit - noise_factor = {noise_factors[i+1]}")
        job = ideal_estimator.run(folded_circuits[i], observable)
        result = job.result()
        ideal_estimations_results.append([result.values[0], result.metadata[0]['variance']])

    pp.pprint(ideal_estimations_results)



    ### == Performing experiments on the noisy simulator == ### 
    print(">> Running experiments on noisy simulator...")
    with Session(service=service, backend=noisy_simulator) as session:
        noisy_estimator = IBMQEstimator(session = session, options = noisy_options)

        print(f">>>> Initial circuit - noise_factor = {noise_factors[0]}")
        job = noisy_estimator.run(circuits = initial_circuit, observables = observable)
        result = job.result()
        noisy_estimations_results.append([result.values[0], result.metadata[0]['variance']])
        
        for i in range(len(folded_circuits)):
            print(f">>>> Folded circuit - noise_factor = {noise_factors[i+1]}")
            job = noisy_estimator.run(folded_circuits[i], observable)
            result = job.result()
            noisy_estimations_results.append([result.values[0], result.metadata[0]['variance']])

        pp.pprint(noisy_estimations_results)



    ### == Performing extrapolation == ###
    print(">> Extrapolating by fitting a function to the data points...")
    ideal_expectation_values = np.array(ideal_estimations_results)[:,0]
    print(ideal_expectation_values)
    ideal_std_deviations = np.sqrt(np.array(ideal_estimations_results)[:,1])
    print(ideal_std_deviations)

    noisy_expectation_values = np.array(noisy_estimations_results)[:,0]
    print(noisy_expectation_values)
    noisy_std_deviations = np.sqrt(np.array(noisy_estimations_results)[:,1])
    print(noisy_std_deviations)

    optimal_coefs, covariance_matrix = polynomial_extrapolation(polynomial_degree, noise_factors, noisy_expectation_values, noisy_std_deviations)
    print(optimal_coefs)
    print(covariance_matrix)
    mitigated_value = optimal_coefs[0]
    perr = np.sqrt(np.diag(covariance_matrix))
    print(f"mitigated_value = {mitigated_value} +/- {perr}")


    print(">> Plotting the data with variances...")
    plt.rcParams["figure.figsize"] = (5,3.5)
    plt.grid(which='major',axis='both')

    plt.errorbar([0, noise_factors[-1]],[ideal_expectation_values[0], ideal_expectation_values[-1]], [ideal_std_deviations[0], ideal_std_deviations[-1]], linestyle="--", label=f"Ideal", color="#000000")
    plt.scatter(0, mitigated_value, label=f"Mitigated", marker="x", color="#785ef0")
    plt.errorbar(noise_factors, noisy_expectation_values, noisy_std_deviations, linestyle='None', marker='.', capsize=3, label=f"Unmitigated", color="#dc267f")
    plt.title("Zero-noise extrapolation - Local folding")
    plt.xlabel("Noise factors")
    plt.ylabel(f"Expectation Value ($\langle {observable.paulis[0]} \\rangle$)")
    plt.legend()
    plt.show()

    plt.plot([0, noise_factors[-1]],[ideal_expectation_values[0], ideal_expectation_values[-1]], linestyle="--", label=f"Ideal", color="#000000")
    plt.scatter(0, mitigated_value, label=f"Mitigated", marker="x", color="#785ef0")
    plt.plot(noise_factors, noisy_expectation_values, linestyle='None', marker='.', label=f"Unmitigated", color="#dc267f")
    plt.title("Zero-noise extrapolation - Local folding")
    plt.xlabel("Noise factors")
    plt.ylabel(f"Expectation Value ($\langle {observable.paulis[0]} \\rangle$)")
    plt.legend()
    plt.show()




    ### == Storage of the data == ###
    print(">> Saving data...")
    print(">>>> Information about the circuits...")
    # save_circuit_data(chosen_U, fault_rates, ...)
    print(">>>> Estimations from the simulations...")
    # save_estimations_results(ideal_estimations_results, noisy_estimations_results)


