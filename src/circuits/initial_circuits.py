# Module: Initial circuits used for global, local and partial foldings
# Author: oanikienko
# Date: 19/11/2023

## == Libraries == ##

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

## == Functions == ##

def U_4qubits(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics
    circuit.cx(q_register[0], q_register[1])
    circuit.cx(q_register[1], q_register[2])
    circuit.cx(q_register[1], q_register[3])

    circuit.cx(q_register[3], q_register[1])
    circuit.cx(q_register[2], q_register[1])
    circuit.cx(q_register[1], q_register[0])

def U_4qubits_dagger(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics
    circuit.cx(q_register[1], q_register[0])
    circuit.cx(q_register[2], q_register[1])
    circuit.cx(q_register[3], q_register[1])
    
    circuit.cx(q_register[1], q_register[3])
    circuit.cx(q_register[1], q_register[2])
    circuit.cx(q_register[0], q_register[1])


def U_5qubits(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics


def U_5qubits_dagger(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics


def build_initial_circuit(qubits_nb, chosen_U):
    #TODO chosen_U = pointeur de fonction (une parmi celles du dessus)

    q_register = QuantumRegister(nb_qubits, name='q')
    
    initial_circuit = QuantumCircuit(q_register)

    chosen_U(initial_circuit, q_register)

    return initial_circuit

