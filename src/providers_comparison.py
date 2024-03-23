# Module: providers_comparison
# Author: oanikienko
# Date: 30/11/2023

# == Libraries == #

from utils import csv_io as io
from circuits import providers
from circuits import initial_circuits as init
from utils import configuration as config

import os
from pathlib import Path
import pprint

from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit.providers.fake_provider import FakeProviderForBackendV2, FakeManilaV2, FakeNairobiV2

# == Functions == #


## == Main program == ##

pp = pprint.PrettyPrinter(indent=3, depth=10, sort_dicts=False) 

print(">> Creation of the circuits and the dictionnaries of gates")
circuit_4qubits = init.build_initial_circuit(4, init.U_4qubits)
gates_4qubits = {'cx': [(0, 1), (1, 2), (1, 3), (3, 1), (2, 1), (1, 0)]}


circuit_5qubits = init.build_initial_circuit(5, init.U_5qubits)
gates_5qubits = {'cx': [(0, 1), (1, 2), (1, 3), (3,4), (4,3), (3, 1), (2, 1), (1, 0)]}


print(circuit_4qubits)
print(circuit_5qubits)


"""
print(">> Comparison between fake_backends from FakeProviderForBackendV2")
fake_provider = FakeProviderForBackendV2()

fake_backends = fake_provider.backends()

selected_backends_for_circuit_4qubits = providers.select_backends_for_circuit(fake_provider, circuit_4qubits)
print(f"Fake backends on which the circuit U_4qubits can be run: {selected_backends_for_circuit_4qubits}")

selected_backends_by_gates_4qubits = providers.select_backends_with_gates(fake_provider, gates_4qubits)
print(f"Fake backends on which the gates can be run: {selected_backends_by_gates_4qubits}")

selected_backends_for_circuit_5qubits = providers.select_backends_for_circuit(fake_provider, circuit_5qubits)
print(f"Fake backends on which the circuit U_5qubits can be run: {selected_backends_for_circuit_5qubits}")

selected_backends_by_gates_5qubits = providers.select_backends_with_gates(fake_provider, gates_5qubits)
print(f"Fake backends on which the gates can be run: {selected_backends_by_gates_5qubits}")

common_backends = list(set(selected_backends_for_circuit_4qubits) & set(selected_backends_for_circuit_5qubits))
print(f"Common fake backends between the two circuits: {common_backends}")
"""

print(">> Comparison between backends from IBM Quantum")

working_directory = os.getcwd()
credentials_configfile = "./credentials.ini"
credentials = config.load_config(working_directory, credentials_configfile)

service = QiskitRuntimeService(
                                channel=credentials["ibm.quantum"]["channel"],
                                token=credentials["ibm.quantum"]["api_token"],
                                instance=credentials["ibm.quantum"]["instance"]
                              )

print(service.instances())
print(service.backends())

gates_4qubits = {'ecr': [(1, 0), (2, 1), (3, 1), (1, 3), (1, 2), (0, 1)]}
gates_5qubits = {'ecr': [(1, 0), (2, 1), (3, 1), (4, 3), (3, 4), (1, 3), (1, 2), (0, 1)]}

ibm_brisbane = providers.search_backend(service, 'ibm_brisbane')
brisbane_ecr_error_rates = providers.get_specific_gates_with_error_rates(ibm_brisbane, 'ecr')
brisbane_ecr_error_rates_set = set(brisbane_ecr_error_rates)

ibm_kyoto = providers.search_backend(service, 'ibm_kyoto')
kyoto_ecr_error_rates = providers.get_specific_gates_with_error_rates(ibm_kyoto, 'ecr')
kyoto_ecr_error_rates_set = set(kyoto_ecr_error_rates)

ibm_osaka = providers.search_backend(service, 'ibm_osaka')
osaka_ecr_error_rates = providers.get_specific_gates_with_error_rates(ibm_osaka, 'ecr')
osaka_ecr_error_rates_set = set(osaka_ecr_error_rates)


backends = [ibm_brisbane, ibm_kyoto, ibm_osaka]
selected_backends_for_circuit_4qubits = providers.select_real_backends_for_circuit(backends, transpiled_circuit_4qubits)
print(f"Backends on which the circuit transpiled_U_4qubits can be run: {selected_backends_for_circuit_4qubits}")

selected_backends_for_circuit_5qubits = providers.select_real_backends_for_circuit(backends, transpiled_circuit_5qubits)
print(f"Backends on which the circuit transpiled_U_5qubits can be run: {selected_backends_for_circuit_5qubits}")

