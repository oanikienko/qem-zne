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

from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit.providers.fake_provider import FakeProviderForBackendV2, FakeManilaV2, FakeNairobiV2

# == Functions == #


## == Main program == ##

print(">> Comparison between fake_backends from FakeProviderForBackendV2")
fake_provider = FakeProviderForBackendV2()

fake_backends = fake_provider.backends()

nb_qubits = 4
circuit = init.build_initial_circuit(nb_qubits, init.U_4qubits)
print(circuit)
# image = circuit.draw('latex')
# image.save("./initial_circuit_4qubits.png")
selected_backends_for_circuit_4qubits = providers.select_backends_for_circuit(fake_provider, circuit)
print(f"Backends on which the circuit U_4qubits can be run: {selected_backends_for_circuit_4qubits}")

gates = {'cx': [(0, 1), (1, 2), (1, 3), (3, 1), (2, 1), (1, 0), (3,4), (4,3)]}
selected_backends_by_gates = providers.select_backends_with_gates(fake_provider, gates)
print(f"Backends on which the gates can be run: {selected_backends_by_gates}")

nb_qubits = 5
circuit = init.build_initial_circuit(nb_qubits, init.U_5qubits)
print(circuit)
# image = circuit.draw('latex')
# image.save("./initial_circuit_5qubits.png")
selected_backends_for_circuit_5qubits = providers.select_backends_for_circuit(fake_provider, circuit)
print(f"Backends on which the circuit U_5qubits can be run: {selected_backends_for_circuit_5qubits}")

# print(selected_backends_for_circuit == selected_backends_by_gates)
common_backends = list(set(selected_backends_for_circuit_4qubits) & set(selected_backends_for_circuit_5qubits))
print(f"Common backends between the two circuits: {common_backends}")


# print(">> Comparison between backends from IBM Cloud")
# working_directory = os.getcwd()
# credentials_configfile = "./credentials.ini"
# credentials = config.load_config(working_directory, credentials_configfile)
# service = QiskitRuntimeService(
#                                 channel=credentials["ibm.cloud"]["channel"],
#                                 token=credentials["ibm.cloud"]["api_key"],
#                                 instance=credentials["ibm.cloud"]["instance"]
#                               )

# print(service.backends())



# print(">> Comparison between backends from IBM Quantum")

# service = QiskitRuntimeService(
#                                 channel=credentials["ibm.quantum"]["channel"],
#                                 token=credentials["ibm.quantum"]["api_token"],
#                                 instance=credentials["ibm.quantum"]["instance"]
#                               )

# # print(service.instances())
# print(service.backends())


# print(providers.search_backend(service, 'ibm_brisbane'))

# print(providers.get_backends(service, ['ibm_brisbane', 'ibm_kyoto']))

