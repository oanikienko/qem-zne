# Module: Initial circuits used for global, local and partial foldings
# Author: oanikienko
# Date: 19/11/2023

## == Libraries == ##

import numpy as np

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from circuits import providers
from qiskit.providers.fake_provider import FakeNairobiV2
import pprint

## == Functions == ##

def transpiled_cx(circuit, q_register, qubit_ctrl, qubit_target):

    circuit.sx(q_register[qubit_ctrl])
    circuit.rz(-np.pi/2, q_register[qubit_ctrl])
    circuit.rz(-np.pi/2, q_register[qubit_target])
    circuit.sx(q_register[qubit_target])
    circuit.rz(-np.pi, q_register[qubit_target])
    circuit.ecr(q_register[qubit_target],q_register[qubit_ctrl]) # because of the little endian of Qiskit
    circuit.rz(-np.pi/2, q_register[qubit_ctrl])
    circuit.sx(q_register[qubit_ctrl])
    circuit.rz(np.pi/2, q_register[qubit_ctrl])
    circuit.rz(np.pi/2, q_register[qubit_target])
    circuit.sx(q_register[qubit_target])
    circuit.rz(np.pi/2, q_register[qubit_target])


def U_4qubits(circuit, q_register):
    circuit.cx(q_register[0], q_register[1])
    circuit.cx(q_register[1], q_register[2])
    circuit.cx(q_register[1], q_register[2])
    circuit.cx(q_register[1], q_register[3])

    circuit.cx(q_register[3], q_register[1])
    circuit.cx(q_register[2], q_register[1])
    circuit.cx(q_register[2], q_register[1])
    circuit.cx(q_register[1], q_register[0])


def U_5qubits(circuit, q_register):

    circuit.cx(q_register[0], q_register[1])
    circuit.cx(q_register[1], q_register[2])
    circuit.cx(q_register[1], q_register[2])
    circuit.cx(q_register[1], q_register[3])
    circuit.cx(q_register[3], q_register[4])

    circuit.cx(q_register[4], q_register[3])
    circuit.cx(q_register[3], q_register[1])
    circuit.cx(q_register[2], q_register[1])
    circuit.cx(q_register[2], q_register[1])
    circuit.cx(q_register[1], q_register[0])


def get_existing_circuits():

    circuit_functions = {
                            "U_4qubits": U_4qubits,
                            "U_5qubits": U_5qubits
                        }

    return circuit_functions


def build_initial_circuit(nb_qubits, chosen_U):

    q_register = QuantumRegister(nb_qubits, name='q')
    
    initial_circuit = QuantumCircuit(q_register)

    chosen_U(initial_circuit, q_register)

    return initial_circuit


## == Tests == ##

if __name__ == "__main__":

    nb_qubits = 4

    circuit = build_initial_circuit(nb_qubits, U_4qubits)

    print(circuit)

