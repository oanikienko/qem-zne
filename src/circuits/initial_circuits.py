# Module: Initial circuits used for global, local and partial foldings
# Author: oanikienko
# Date: 19/11/2023

## == Libraries == ##

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

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


# def U_4qubits_dagger(circuit, q_register): #TODO get it with U_4qubits.inverse()
#     ## TODO Adapt it according to the providers chosen with the respect of their characteristics

#     gates = [] # For local folding

#     circuit.cx(q_register[1], q_register[0])
#     gates.append(("cx", 1, 0)
#     circuit.cx(q_register[2], q_register[1])
#     circuit.cx(q_register[3], q_register[1])
    
#     circuit.cx(q_register[1], q_register[3])
#     circuit.cx(q_register[1], q_register[2])
#     circuit.cx(q_register[0], q_register[1])

#     return gates


# def U_5qubits(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics


# def U_5qubits_dagger(circuit, q_register):
    ## TODO Adapt it according to the providers chosen with the respect of their characteristics


def calculate_fault_rate(circuit_gates, provider_backend, noise_factor):

    # TODO récupérer les portes du circuit pour calculer ensuite le bruit
    # TODO récupérer les taux d'erreur pour ce circuit (utils/providers.py)
    # TODO calculer le taux d'erreur

    # cx_error_rates = get_gate_error_rates(provider_backend, "cx")

    circuit_error_rate = 0
    # circuit_1folded_error_rate_l = noise_factor*cx_error_rates[(0,1)] + noise_factor*cx_error_rates[(1,2)] +  noise_factor*cx_error_rates[(1,3)] \
                    # + noise_factor*cx_error_rates[(3,5)] +  noise_factor*cx_error_rates[(5,4)] + noise_factor*cx_error_rates[(5,6)] \
                    # + noise_factor*cx_error_rates[(6,5)] + noise_factor*cx_error_rates[(5,4)] + noise_factor*cx_error_rates[(5,3)] \
                    # + noise_factor*cx_error_rates[(3,1)] + noise_factor*cx_error_rates[(2,1)] + noise_factor*cx_error_rates[(1,0)]
    
    return circuit_error_rate
    

def build_initial_circuit(nb_qubits, chosen_U):
    #TODO chosen_U = pointeur de fonction (une parmi celles du dessus)

    q_register = QuantumRegister(nb_qubits, name='q')
    
    initial_circuit = QuantumCircuit(q_register)

    chosen_U(initial_circuit, q_register)

    return initial_circuit

