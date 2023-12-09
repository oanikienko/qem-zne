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

filename = "../data/fake_providers_V2_csv"
headers = ["name", "version", "online_date", "num_qubits", "possible_operations", "operations_with_error_rates"]
data = []

for fake_backend in fake_backends:
    info = providers.get_backend_info(fake_backend)
    # print(providers.get_operations_with_error_rates(fake_backend))
    # row = [info['name'], info ['version'], info['online_date'], info['num_qubits'], info['operation_names'], providers.get_operations_with_error_rates(fake_backend)]
    # data.append(row)

# io.store_data(headers, data, filename, separator=';')


#TODO real providers (attention au temps d'exécution !)
print(">> Comparison between backends from IBM Cloud")
working_directory = os.getcwd()
credentials_configfile = "./credentials.ini"
credentials = config.load_config(working_directory, credentials_configfile)
service = QiskitRuntimeService(
                                channel=credentials["ibm.cloud"]["channel"],
                                token=credentials["ibm.cloud"]["api_key"],
                                instance=credentials["ibm.cloud"]["instance"]
                              )

print(service.backends())



print(">> Comparison between backends from IBM Quantum")

service = QiskitRuntimeService(
                                channel=credentials["ibm.quantum"]["channel"],
                                token=credentials["ibm.quantum"]["api_token"],
                                instance=credentials["ibm.quantum"]["instance"]
                              )

# print(service.instances())
print(service.backends())


print(providers.search_backend(service, 'ibm_brisbane'))

print(providers.get_backends(service, ['ibm_brisbane', 'ibm_kyoto']))

