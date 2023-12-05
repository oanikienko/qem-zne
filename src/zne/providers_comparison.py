# Module: providers_comparison
# Author: oanikienko
# Date: 30/11/2023

# == Libraries == #

from utils import csv_io as io
from circuits import providers

from pathlib import Path
from circuits import initial_circuits as init
from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit.providers.fake_provider import FakeProviderForBackendV2, FakeManilaV2, FakeNairobiV2
import pprint

# == Functions == #


## == Main program == ##

print(">> Comparison between fake_backends from FakeProviderForBackendV2")
fake_provider = FakeProviderForBackendV2()

fake_backends = fake_provider.backends()

filename = "../data/fake_providers_V2_csv"
headers = ["name", "version", "online_date", "num_qubits", "possible_operations", "operations_with_error_rates"]
data = []

for fake_backend in fake_backends:
    info = providers.get_backend_info(fake_backend)
    # print(providers.get_operations_with_error_rates(fake_backend))
    row = [info['name'], info ['version'], info['online_date'], info['num_qubits'], info['operation_names'], providers.get_operations_with_error_rates(fake_backend)]
    data.append(row)

io.store_data(headers, data, filename, separator=';')


#TODO real providers (attention au temps d'exécution !)
