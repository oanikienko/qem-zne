# Script: Implementation of the zero-noise extrapolation (custom implementation, from scratch)
# Author: oanikienko
# Date: 05/12/2023

## === Libraries === ##

from utils.time_measurement import measure_job_execution_time
from extrapolation.polynomial_extrapolation import polynomial_extrapolation

import numpy as np

# from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, transpile, execute
# from qiskit.tools.monitor import job_monitor
# from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session

from qiskit import transpile
from qiskit_ibm_runtime import Session
from qiskit_ibm_runtime import Estimator as IBMQEstimator
from qiskit_ibm_runtime.options import TranspilationOptions


## === Functions === ##

def run_experiment(service, common_parameters, observable, session_backend, estimator_options, run_only_on_simulator, initial_circuit, folded_circuits, estimations, execution_times):

    print(estimator_options)
    print(estimator_options.transpilation)

    #=== Beginning of the session for the initial circuit ===#
    with Session(service = service, backend = session_backend) as session:
        estimator = IBMQEstimator(session = session, options = estimator_options)
        print(estimator)

        print(f"\t\t\t\t\t>> Initial circuit - noise_factor = {common_parameters['noise_factors'][0]}")
        # NoiseModel
        if run_only_on_simulator:
            job = estimator.run(initial_circuit, observable)
            result = job.result()

        # Real device
        elif session_backend.name != "ibmq_qasm_simulator":
            transpiled_circuit = transpile(initial_circuit, session_backend)
            job = estimator.run(transpiled_circuit, observable)
            result = job.result()
            print(result)

        # Fake device
        else:
            job = estimator.run(initial_circuit, observable)
            result = job.result()


        total_time, quantum_time = measure_job_execution_time(job)

        execution_times[common_parameters["noise_factors"][0]] = {"total_time": float(total_time.total_seconds()), "quantum_time": float(quantum_time)}
        estimations[common_parameters["noise_factors"][0]] = [float(result.values[0]), float(result.metadata[0]['variance'])]

    #=== End of the session for the initial circuit ===#

    for i in range(len(folded_circuits)):
        #=== Beginning of the session for the i-th folded circuit ===#
        with Session(service = service, backend = session_backend) as session:
            estimator = IBMQEstimator(session = session, options = estimator_options)
            print(estimator)

            print(f"\t\t\t\t\t>> Folded circuit - noise_factor = {common_parameters['noise_factors'][i+1]}")
            # NoiseModel
            if run_only_on_simulator:
                job = estimator.run(folded_circuits[i], observable)
                result = job.result()

            # Real device
            elif session_backend.name != "ibmq_qasm_simulator":
                transpiled_circuit = transpile(folded_circuits[i], session_backend)
                job = estimator.run(transpiled_circuit, observable)
                result = job.result()

            # Fake device
            else:
                job = estimator.run(folded_circuits[i], observable)
                result = job.result()

            total_time, quantum_time = measure_job_execution_time(job)

            execution_times[common_parameters["noise_factors"][i+1]] = {"total_time": float(total_time.total_seconds()), "quantum_time": float(quantum_time)}
            estimations[common_parameters["noise_factors"][i+1]] = [float(result.values[0]), float(result.metadata[0]['variance'])]

        #=== End of the session for the i-th folded circuit ===#



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
                extrapolation_results["degrees"][degree] = dict()

                optimal_coefs, covariance_matrix = experiment["extrapolations"][i]["function"](degree, fault_rates_values, noisy_expectation_values, noisy_std_deviations)
                coefs_variances = np.diag(covariance_matrix)

                extrapolation_results["degrees"][degree]["optimal_coefs"] = [float(optimal_coef) for optimal_coef in optimal_coefs]
                extrapolation_results["degrees"][degree]["coefs_variances"] = [float(variance) for variance in coefs_variances]

        elif experiment["extrapolations"][i]["type"] == "exponential":
            extrapolation_results["type"] = "exponential"
            optimal_coefs, covariance_matrix = experiment["extrapolations"][i]["function"](fault_rates_values, noisy_expectation_values, noisy_std_deviations)
            coefs_variances = np.diag(covariance_matrix)

            extrapolation_results["optimal_coefs"] = [float(optimal_coef) for optimal_coef in optimal_coefs]
            extrapolation_results["coefs_variances"] = [float(variance) for variance in coefs_variances]


        # Adding the new extrapolation result in the list
        extrapolations_results.append(extrapolation_results)


    return extrapolations_results




