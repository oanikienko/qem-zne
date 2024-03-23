# Script: Main program for applying various implementations of zero-noise extrapolation
# Author: oanikienko
# Date: 02/01/2024

## === Libraries === ##

from utils import configuration as config
from utils import parameter_setup as parameters
from circuits import initial_circuits as init
from circuits import noise_boosting
from circuits import providers
from utils import yaml_io 
from utils.time_measurement import measure_job_execution_time
from customZNE.extrapolation.polynomial_extrapolation import polynomial_extrapolation
import customZNE.custom_zne as customZNE

import sys
import pprint
import os
from pathlib import Path

from qiskit import transpile
from qiskit.quantum_info import SparsePauliOp

from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit_ibm_runtime import Estimator as IBMQEstimator

from qiskit.providers.aer.noise import NoiseModel


## === Functions === ##

## ==== File management ==== ##

def get_experiments_configfile(argv):
    if len(argv) < 2:
        print("Error: An experiments configuration file is required.")
        sys.exit()
    elif len(argv) > 2:
        print("Error: Only 1 experiments configuration file is accepted.")
        sys.exit()
    
    return argv[1]


def filename_from_path(file_path):
    return Path(file_path).stem


def define_experiments_datafile(experiments_configfile):

    experiments_filename = filename_from_path(experiments_configfile)

    return f"./data/{experiments_filename}_results.yaml"



## ==== Parameter setup ==== ##

def set_up_parameters(ibm_quantum_service, experiments_configuration):

    common_parameters = dict()
    providers_parameters = dict()
    experiments_parameters = []

    # Selecting the ZNE implementation
    parameters.set_up_implementation(experiments_configuration, common_parameters)

    # Defining the circuit to use for experiments
    parameters.set_up_circuit(experiments_configuration, common_parameters)

    # Defining the number of qubits
    parameters.set_up_num_qubits(experiments_configuration, common_parameters)

    # Defining the observable 
    parameters.set_up_observable(experiments_configuration, common_parameters)

    # Defining the noise factors
    parameters.set_up_noise_factors(experiments_configuration, common_parameters)

    # Defining the providers and their backends
    parameters.set_up_providers_and_backends(ibm_quantum_service, experiments_configuration, providers_parameters)

    # Defining the list for the experiments 
    parameters.set_up_experiments(experiments_configuration, experiments_parameters)

    return common_parameters, providers_parameters, experiments_parameters


## ==== Utilities ==== ##

def print_experiment(experiment, tab_level):

    print(f"{tab_level}>> Current experiment:")
    try:
        print(f"{tab_level}\t - boost_method: {experiment['boost_method'].__name__}")
    except AttributeError:
        print(f"{tab_level}\t - boost_method: {experiment['boost_method']}")

    print(f"{tab_level}\t - nb_shots: {experiment['nb_shots']}")
    print(f"{tab_level}\t - extrapolations:")

    for extrapolation in experiment["extrapolations"]:
        print(f"{tab_level}\t\t - {extrapolation['type']}, with the following parameters:")
        if extrapolation.get('parameters') is not None:
            for key in extrapolation['parameters'].keys():
                print(f"{tab_level}\t\t\t - {key} = {extrapolation['parameters'][key]}")


def create_folded_circuit(common_parameters, experiment, initial_circuit, noise_factor):

    # === customZNE === #
    if common_parameters["implementation"] == "customZNE":
        return experiment["boost_method"](initial_circuit, noise_factor)

    # === qiskitZNE === #
    elif common_parameters["implementation"] == "qiskitZNE":
        return noise_boosting.local_folding(initial_circuit, noise_factor)


def compute_fault_rates(initial_circuit, folded_circuits, backend, common_parameters):
    
    fault_rates = dict()

    fault_rates[common_parameters["noise_factors"][0]] = providers.calculate_error_rate(initial_circuit, backend, common_parameters["noise_factors"][0])

    for i in range(len(folded_circuits)):
        fault_rates[common_parameters["noise_factors"][i+1]] = providers.calculate_error_rate(folded_circuits[i], backend, common_parameters["noise_factors"][i+1])

    return fault_rates

def create_observable(common_parameters, noisy_backend):

    observable_name = common_parameters["observable"]

    if noisy_backend.name == "ibmq_qasm_simulator":
        common_parameters["observable"] = SparsePauliOp(observable_name*common_parameters["nb_qubits"])
    else:
        common_parameters["observable"] = SparsePauliOp(observable_name*noisy_backend.num_qubits)
    

def initialize_experiments_results(results):

    results["experiments_results"] = []


def initialize_estimations(estimations):

    estimations["ideal_backend"] = dict() 
    estimations["noisy_backend"] = dict() 


def initialize_execution_times(execution_times):

    execution_times["ideal_backend"] = dict() 
    execution_times["noisy_backend"] = dict() 


def initialize_sessions_parameters(sessions_parameters):

    sessions_parameters["service"] = None
    sessions_parameters["ideal_session"] = dict()
    sessions_parameters["noisy_session"] = dict()



def define_service(service, sessions_parameters):
    sessions_parameters["service"] = ibm_quantum_service


def define_backends(service, provider_name, run_only_on_simulator, backend, sessions_parameters):

    # Defining the backend for the session on ideal simulator
    sessions_parameters["ideal_session"]["backend"] = service.get_backend("ibmq_qasm_simulator") 

    # Defining the backend for the session on noisy simulator or real device
    if run_only_on_simulator:
        sessions_parameters["noisy_session"]["backend"] = service.get_backend("ibmq_qasm_simulator")
        sessions_parameters["noisy_session"]["run_only_on_simulator"] = run_only_on_simulator

    elif provider_name == "fake_provider": 
        sessions_parameters["noisy_session"]["backend"] = service.get_backend("ibmq_qasm_simulator") 

    elif provider_name == "ibm_quantum_provider":
        sessions_parameters["noisy_session"]["backend"] = backend


def create_options(nb_shots, common_parameters, experiment, backend = None):

    options = Options()
    options.execution.shots = nb_shots
    options.optimization_level = common_parameters["optimization_level"]
    options.resilience_level = common_parameters["resilience_level"]

    if common_parameters["implementation"] == "qiskitZNE":
        options.resilience.noise_factors = tuple(common_parameters["noise_factors"])
        options.resilience.noise_amplifier = experiment["boost_method"]
        options.resilience.extrapolator = experiment["extrapolations"][0]["function"] # Only 1 extrapolation per experiment with qiskitZNE

    if backend != None:
        options.simulator = {
                "noise_model": NoiseModel.from_backend(backend),
                "basis_gates": backend.operation_names,
                "coupling_map": backend.coupling_map
        }
        print(backend.name)
        print(options.simulator)

    return options


def define_options(nb_shots, common_parameters, experiment, sessions_parameters):
    
    # Defining the options for the session on ideal simulator
    sessions_parameters["ideal_session"]["options"] = create_options(nb_shots, common_parameters, experiment)

    # Defining the options for the session on noisy simulator or real device
    sessions_parameters["noisy_session"]["options"] = create_options(nb_shots, common_parameters, experiment, backend)



## ==== Backup of the results ==== ##

def save_common_parameters(common_parameters, results):
    
    results["circuit"] = common_parameters["circuit"].__name__
    results["nb_qubits"] = common_parameters["nb_qubits"]
    results["observable"] = common_parameters["observable"]
    results["optimization_level"] = common_parameters["optimization_level"]
    results["resilience_level"] = common_parameters["resilience_level"]


def save_experiment_data(common_parameters, provider_name, backend, experiment, nb_shots, fault_rates, estimations, execution_times, extrapolations_results, results):

    experiment_results = dict()

    experiment_results["provider"] = provider_name
    experiment_results["backend"] = backend.name
    experiment_results["nb_shots"] = nb_shots

    if common_parameters["implementation"] == "customZNE":
        experiment_results["boost_method"] = experiment["boost_method"].__name__    
    else:
        experiment_results["boost_method"] = experiment["boost_method"]


    experiment_results["circuit_results"] = []

    if common_parameters["implementation"] == "customZNE":
        
        for noise_factor in fault_rates.keys():
            circuit_results = dict()

            circuit_results["noise_factor"] = noise_factor
            circuit_results["fault_rate"] = fault_rates[noise_factor]

            circuit_results["execution_times"] = {"ideal_backend": {"total_time": execution_times["ideal_backend"][noise_factor]["total_time"],
                                                                       "quantum_time": execution_times["ideal_backend"][noise_factor]["quantum_time"]
                                                                      },
                                                  "noisy_backend": {"total_time": execution_times["noisy_backend"][noise_factor]["total_time"],
                                                                      "quantum_time": execution_times["noisy_backend"][noise_factor]["quantum_time"]
                                                                     }
                                                  }

            circuit_results["ideal_expectation_value"] = estimations["ideal_backend"][noise_factor][0]
            circuit_results["ideal_variance"] = estimations["ideal_backend"][noise_factor][1]

            circuit_results["noisy_expectation_value"] = estimations["noisy_backend"][noise_factor][0]
            circuit_results["noisy_variance"] = estimations["noisy_backend"][noise_factor][1]

            experiment_results["circuit_results"].append(circuit_results)

       
    elif common_parameters["implementation"] == "qiskitZNE":

        experiment_results["execution_times"] = {"ideal_backend": {"total_time": execution_times["ideal_backend"][1]["total_time"],
                                                                       "quantum_time": execution_times["ideal_backend"][1]["quantum_time"]
                                                                      },
                                                  "noisy_backend": {"total_time": execution_times["noisy_backend"][1]["total_time"],
                                                                      "quantum_time": execution_times["noisy_backend"][1]["quantum_time"]
                                                                     }
                                                  }

        for noise_factor in fault_rates.keys():
            circuit_results = dict()

            circuit_results["noise_factor"] = noise_factor
            circuit_results["fault_rate"] = fault_rates[noise_factor]

            circuit_results["ideal_expectation_value"] = estimations["ideal_backend"][noise_factor][0]
            circuit_results["ideal_variance"] = estimations["ideal_backend"][noise_factor][1]

            circuit_results["noisy_expectation_value"] = estimations["noisy_backend"][noise_factor][0]
            circuit_results["noisy_variance"] = estimations["noisy_backend"][noise_factor][1]

            experiment_results["circuit_results"].append(circuit_results)

    experiment_results["extrapolations_results"] = extrapolations_results

    results["experiments_results"].append(experiment_results)


## ==== Implementations of the ZNE ==== ##

def apply_customZNE(service, common_parameters, experiment, sessions_parameters, initial_circuit, folded_circuits, fault_rates, estimations, execution_times):


    # Defining the observable according to the backend
    ideal_backend_observable = SparsePauliOp(common_parameters["observable"]*common_parameters["nb_qubits"])

    noisy_backend_observable = None

    # Real device
    if sessions_parameters["noisy_session"]["backend"].name != "ibmq_qasm_simulator":
        noisy_backend_observable = SparsePauliOp(common_parameters["observable"]*sessions_parameters["noisy_session"]["backend"].num_qubits)

    # NoiseModel and fake device
    else:
        noisy_backend_observable = ideal_backend_observable


    #### == Performing experiments on the ideal backend == ### 

    print("\t\t\t\t>> Running experiments on ideal backend...")
    customZNE.run_experiment(service, common_parameters, ideal_backend_observable,
                             sessions_parameters["ideal_session"]["backend"], 
                             sessions_parameters["ideal_session"]["options"], 
                             False,
                             initial_circuit, folded_circuits, 
                             estimations["ideal_backend"], execution_times["ideal_backend"])



    #### == Performing experiments on the noisy backend == ### 

    print("\t\t\t\t>> Running experiments on noisy backend...")
    if sessions_parameters["noisy_session"].get("run_only_on_simulator") is True:
        customZNE.run_experiment(service, common_parameters, noisy_backend_observable,
                                 sessions_parameters["noisy_session"]["backend"], 
                                 sessions_parameters["noisy_session"]["options"], 
                                 sessions_parameters["noisy_session"]["run_only_on_simulator"],
                                 initial_circuit, folded_circuits, 
                                 estimations["noisy_backend"], execution_times["noisy_backend"])
    else:
        customZNE.run_experiment(service, common_parameters, noisy_backend_observable,
                                 sessions_parameters["noisy_session"]["backend"], 
                                 sessions_parameters["noisy_session"]["options"], 
                                 False,
                                 initial_circuit, folded_circuits, 
                                 estimations["noisy_backend"], execution_times["noisy_backend"])



    #### == Performing extrapolation == ###
    print("\t\t\t\t>> Extrapolating by fitting various functions to the data points...")

    extrapolations_results = customZNE.extrapolate(fault_rates, estimations["ideal_backend"], estimations["noisy_backend"], experiment)

    return extrapolations_results



def apply_qiskitZNE(service, common_parameters, experiment, sessions_parameters, initial_circuit, folded_circuits, fault_rates, estimations, execution_times):


    # Initializing variables
    extrapolations_results = []

    ideal_expectation_value = 0
    noisy_expectation_value = 0


    # Defining the observable according to the backend
    ideal_backend_observable = SparsePauliOp(common_parameters["observable"]*common_parameters["nb_qubits"])

    noisy_backend_observable = None

    if sessions_parameters["noisy_session"]["backend"].name != "ibmq_qasm_simulator":
        noisy_backend_observable = SparsePauliOp(common_parameters["observable"]*sessions_parameters["noisy_session"]["backend"].num_qubits)

    else:
        noisy_backend_observable = ideal_backend_observable



    #### == Performing experiments on the ideal backend == ### 

    print("\t\t\t\t>> Running experiments on ideal backend...")
    with Session(service = service, backend = sessions_parameters["ideal_session"]["backend"]) as session:
        estimator = IBMQEstimator(session = session, options = sessions_parameters["ideal_session"]["options"])

        job = estimator.run(initial_circuit, ideal_backend_observable)
        result = job.result()

        total_time, quantum_time = measure_job_execution_time(job)
        
        noise_factors = result.metadata[0]["zne"]["noise_amplification"]["noise_factors"]
        ideal_values = result.metadata[0]["zne"]["noise_amplification"]["values"]
        ideal_variances = result.metadata[0]["zne"]["noise_amplification"]["variance"]

        for i in range(0, len(noise_factors)):
            estimations["ideal_backend"][noise_factors[i]] = [float(ideal_values[i]), float(ideal_variances[i])]

        execution_times["ideal_backend"][common_parameters["noise_factors"][0]] = {"total_time": float(total_time.total_seconds()), "quantum_time": float(quantum_time)}
    
        ideal_expectation_value = result.values[0]


    #### == Performing experiments on the noisy backend == ### 

    print("\t\t\t\t>> Running experiments on noisy backend...")
    with Session(service = service, backend = sessions_parameters["noisy_session"]["backend"]) as session:
        estimator = IBMQEstimator(session = session, options = sessions_parameters["noisy_session"]["options"])

        # NoiseModel
        if sessions_parameters["noisy_session"].get("run_only_on_simulator") is True:
            transpiled_circuit = transpile(initial_circuit, sessions_parameters["noisy_session"]["backend"])
            job = estimator.run(transpiled_circuit, noisy_backend_observable)
            result = job.result()

        # Real device
        elif sessions_parameters["noisy_session"]["backend"].name != "ibmq_qasm_simulator":
            transpiled_circuit = transpile(initial_circuit, sessions_parameters["noisy_session"]["backend"])
            job = estimator.run(transpiled_circuit, noisy_backend_observable)
            result = job.result()

        # Fake device
        else:
            job = estimator.run(initial_circuit, noisy_backend_observable)
            result = job.result()

        total_time, quantum_time = measure_job_execution_time(job)

        noise_factors = result.metadata[0]["zne"]["noise_amplification"]["noise_factors"]
        noisy_values = result.metadata[0]["zne"]["noise_amplification"]["values"]
        noisy_variances = result.metadata[0]["zne"]["noise_amplification"]["variance"]

        for i in range(0, len(noise_factors)):
            estimations["noisy_backend"][noise_factors[i]] = [float(noisy_values[i]), float(noisy_variances[i])]

        execution_times["noisy_backend"][common_parameters["noise_factors"][0]] = {"total_time": float(total_time.total_seconds()), "quantum_time": float(quantum_time)}

        noisy_expectation_value = result.values[0]


    #### == Getting extrapolation results == ### 

    extrapolation_results = dict()

    extrapolation_results["type"] = "polynomial"
    extrapolation_results["p0"] = None

    extrapolation_results["degrees"] = dict()

    degree = experiment["extrapolations"][0]["parameters"]["degrees"][0]

    extrapolation_results["degrees"][degree] = dict()

    extrapolation_results["degrees"][degree]["ideal_expectation_value"] = float(ideal_expectation_value)
    extrapolation_results["degrees"][degree]["noisy_expectation_value"] = float(noisy_expectation_value)


    extrapolations_results.append(extrapolation_results)

    return extrapolations_results

def get_existing_ZNEs():

    existing_ZNEs = { 
                        "customZNE": apply_customZNE,
                        "qiskitZNE": apply_qiskitZNE
                    }

    return existing_ZNEs

def select_ZNE_implementation(common_parameters):

    existing_ZNEs = get_existing_ZNEs()
    try:
        return existing_ZNEs[common_parameters["implementation"]]
    except KeyError:
        print("Error: the implementation {0} does not exist.".format(common_parameters["implementation"]))
        sys.exit()



## === Global parameters === ##

pp = pprint.PrettyPrinter(indent=3, depth=10, sort_dicts=False)

working_directory = os.getcwd()

global_params_configfile = "./parameters/global_parameters.ini"
credentials_configfile = "./credentials.ini"

experiments_configfile = get_experiments_configfile(sys.argv) 
experiments_datafile = define_experiments_datafile(experiments_configfile)


## === Main program === ##


### == Loading of the configuration files == ###

print(">> Loading configurations...")

global_params = config.load_config(working_directory, global_params_configfile)
credentials = config.load_config(working_directory, credentials_configfile)

experiments_configuration = yaml_io.load_data(working_directory, experiments_configfile)


if not config.loaded_configurations(global_params, credentials):
    print("Error: at least one configuration is empty. Please check your *.ini and *.yaml files (filepaths, permissions and syntax).")
    sys.exit()

else: 
    ### == Connection to IBM services == ### 
    print(">> Connecting to IBM Quantum...")
    ibm_quantum_service = QiskitRuntimeService(
                                channel=credentials["ibm.quantum"]["channel"],
                                token=credentials["ibm.quantum"]["api_token"],
                                instance=credentials["ibm.quantum"]["instance"]
                              )

    ### == Setup of the experiments == ### 
    print(">> Getting parameters...")

    common_parameters, providers_parameters, experiments_parameters = set_up_parameters(ibm_quantum_service, experiments_configuration)

    pp.pprint(common_parameters)
    pp.pprint(providers_parameters)
    pp.pprint(experiments_parameters)


    print(">> Initializing the results for this run...")
    results = dict()

    print(">> Storing common parameters in the results...")
    save_common_parameters(common_parameters, results)


    #### == Construction of the circuits == ### 
    print(">> Building the initial circuit...")
    initial_circuit = init.build_initial_circuit(common_parameters["nb_qubits"], common_parameters["circuit"])

    ##### == Execution of the experiments on the backends == ####
    
    print(">> Executing the experiments on the backends...")

    initialize_experiments_results(results)

    for provider_name in providers_parameters.keys():

        if providers_parameters[provider_name].get("run_only_on_simulator") is not None:
            run_only_on_simulator = providers_parameters[provider_name]["run_only_on_simulator"]
        else:
            run_only_on_simulator = False

        print(f"\t>> Current provider: {provider_name}")
        

        for backend in providers_parameters[provider_name]["backends_objects"]:
            print(f"\t\t>> Current backend: {backend.name}")

            if providers_parameters[provider_name].get("run_only_on_simulator") is not None:
                print(f"\t\t>> Running only on simulator: {run_only_on_simulator}")

            for experiment in experiments_parameters:

                print_experiment(experiment, "\t\t\t")

                print("\t\t\t>> Initializing the variables for the current experiment...")
                
                folded_circuits = []
                transpiled_circuits = []

                fault_rates = dict()

                estimations = dict()
                execution_times = dict()

                initialize_estimations(estimations)
                initialize_execution_times(execution_times)


                print("\t\t\t>> Creating the circuits for the current experiment...")
                for noise_factor in common_parameters["noise_factors"][1:]:
                   folded_circuits.append(create_folded_circuit(common_parameters, experiment, initial_circuit, noise_factor))


                if provider_name == "fake_provider": 
                    print("\t\t\t>> Computing the fault rate for each circuit...")
                    fault_rates = compute_fault_rates(initial_circuit, folded_circuits, backend, common_parameters)
            
                elif provider_name == "ibm_quantum_provider":
                    print("\t\t\t>> Transpiling circuits on real backend...")
                    transpiled_initial_circuit = transpile(initial_circuit, backend)
                    transpiled_circuits.append(transpiled_initial_circuit)

                    for circuit in folded_circuits:
                        transpiled_folded_circuit = transpile(circuit, backend)
                        transpiled_circuits.append(transpiled_folded_circuit)
                    
                    print("\t\t\t>> Computing the fault rate for each circuit...")
                    for i in range(0, len(transpiled_circuits)):
                        fault_rates[common_parameters["noise_factors"][i]] = providers.calculate_fault_rate(transpiled_circuits[i], backend)


                for nb_shots in experiment["nb_shots"]:
                    print(f"\t\t\t\t>> nb_shots = {nb_shots}")

                    print(">> Initializing parameters of the sessions...")

                    sessions_parameters = dict()
                    initialize_sessions_parameters(sessions_parameters)

                    #### == Setup of the backend == ### 
                    print("\t\t\t\t>> Defining the backends...")

                    define_service(ibm_quantum_service, sessions_parameters)
                    define_backends(ibm_quantum_service, provider_name, run_only_on_simulator, backend, sessions_parameters)


                    #### == Estimation of the expectation value on the ideal backend, without QEM == ### 
                    print("\t\t\t\t>> Setting up estimators' options...")

                    define_options(nb_shots, common_parameters, experiment, sessions_parameters)

                    selectedZNE = select_ZNE_implementation(common_parameters)

                    extrapolations_results = selectedZNE(ibm_quantum_service, common_parameters, experiment, sessions_parameters, initial_circuit, folded_circuits, fault_rates, estimations, execution_times)
                   

                    #### == Save data for the current experiment == ### 

                    save_experiment_data(common_parameters, provider_name, backend, experiment, nb_shots, fault_rates, estimations, execution_times, extrapolations_results, results)



###### == Storage of the data == ###
print(">> Saving data...")
pp.pprint(results)
yaml_io.store_data(results, working_directory, experiments_datafile)




