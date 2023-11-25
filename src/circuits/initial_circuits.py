# Module: Initial circuits used for global, local and partial foldings
# Author: oanikienko
# Date: 19/11/2023

## == Libraries == ##

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from circuits import providers
from qiskit.providers.fake_provider import FakeNairobiV2
import pprint

## == Functions == ##

def U_4qubits(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics
    # For local folding => needs a parser to implement all kinds of gates (x, y, z, s, cx, cz, cy, h, ..., with the correct number of qubits (1, 2, 3...))

    # circuit.s(q_register[0]) # TODO test only
    circuit.cx(q_register[0], q_register[1])
    circuit.cx(q_register[1], q_register[2])
    circuit.cx(q_register[1], q_register[3])

    circuit.cx(q_register[3], q_register[1])
    circuit.cx(q_register[2], q_register[1])
    circuit.cx(q_register[1], q_register[0])



# def U_5qubits(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics




def build_initial_circuit(nb_qubits, chosen_U):
    #TODO chosen_U = pointeur de fonction (une parmi celles du dessus)

    q_register = QuantumRegister(nb_qubits, name='q')
    
    initial_circuit = QuantumCircuit(q_register)

    chosen_U(initial_circuit, q_register)

    return initial_circuit


## == Tests == ##

if __name__ == "__main__":

    nb_qubits = 4

    circuit = build_initial_circuit(nb_qubits, U_4qubits)

    print(circuit)

