# Script: Implementation of the zero-noise extrapolation
#         using global folding to boost the noise
# Author: oanikienko
# Date: 21/11/2O23

## == Libraries == ##

from utils import configuration as configuration
from circuits import initial_circuits as init
from circuits import folding

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, transpile, execute
from qiskit.tools.visualization import plot_histogram

from qiskit_aer import AerSimulator
from qiskit_aer.primitives import Estimator as AerEstimator
from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.fake_provider import FakeNairobiV2

from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit_ibm_runtime import Estimator as IBMQEstimator
from qiskit.primitives import Estimator, BackendEstimator
from qiskit.quantum_info import SparsePauliOp


## == Global parameters == ##

mpl.rcParams["figure.dpi"] = 300
plt.rcParams.update({"text.usetex": True, "font.family": "Computer Modern Roman"})


## == Functions == ##


## == Main program == ##

print(">> Defining the .ini file to use...")
filepath = "./credentials.ini"

print(">> Loading the configuration...")
config = configuration.load_config(filepath)

if not configuration.is_empty(config):
    print(">> Connecting to IBM Cloud...")
    # service = QiskitRuntimeService(channel=config["ibmq.cloud"]["channel"], token=config["ibmq.cloud"]["API_key"], instance=config["ibmq.cloud"]["instance"])
    # configuration.print_config(config)

    # TODO modifier nb_qubits en récupérant la valeur stockée dans les fichiers .ini
    nb_qubits = 4
    initial_circuit = init.build_initial_circuit(nb_qubits, init.U_4qubits)
    print(initial_circuit)

    # fig = initial_circuit.draw('mpl')
    # plt.show()
    
    # TODO modifier noise_factors pour récupérer la valeur stockée dans les fichiers .ini
    noise_factors = [3, 5, 7]
    folded_circuits = []

    for noise_factor in noise_factors:
        folded_circuits.append(folding.global_folding(initial_circuit, nb_qubits, noise_factor))

    for i in range(len(folded_circuits)):
        print(folded_circuits[i])


else:
    print(">> Error: {0} not found.".format(filepath))

