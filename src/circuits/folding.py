# Module: Folding - repeat gates unitarily to boost noise in the circuit
#         Implements the following methods: global folding, local folding
# Date: 23/11/2023


## == Libraries == ##

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from circuits import initial_circuits as init

## == Functions == ##

def global_folding(initial_circuit, nb_qubits, noise_factor):

    folded_circuit = QuantumCircuit(nb_qubits)

    for i in range(1, noise_factor+1):
        if i % 2 != 0:
            folded_circuit.compose(initial_circuit, inplace=True)
        else: 
            folded_circuit.compose(initial_circuit.inverse(), inplace=True)

    return folded_circuit

def local_folding(initial_circuit, nb_qubits, noise_factor):

    q_register = QuantumRegister(nb_qubits, name='q')

    folded_circuit = QuantumCircuit(q_register)
    
    circuit_instructions = []
    for circuit_instruction in initial_circuit.data:
        circuit_instructions.append(circuit_instruction)

    for i in range(0,len(circuit_instructions)):
        circuit_instruction = circuit_instructions[i]

        folded_circuit.append(circuit_instruction.operation, qargs=circuit_instruction.qubits, cargs=circuit_instruction.clbits)
        for i in range(1,noise_factor):
            if i%2 != 0:
                folded_circuit.append(circuit_instruction.operation.inverse(), qargs=circuit_instruction.qubits, cargs=circuit_instruction.clbits)
            else:
                folded_circuit.append(circuit_instruction.operation, qargs=circuit_instruction.qubits, cargs=circuit_instruction.clbits)

    return folded_circuit 

## == Tests == ##

if __name__ == "__main__":

    nb_qubits = 4
    noise_factors = [1,3,5]

    print(">> Initial circuit")
    initial_circuit = init.build_initial_circuit(nb_qubits, init.U_4qubits)
    print(initial_circuit)

    print(">> Global folding")
    folded_circuits = []
    for factor in noise_factors[1:]:
        folded_circuits.append(global_folding(initial_circuit, nb_qubits, factor))

    for i in range(len(folded_circuits)):
        print(folded_circuits[i])

    print(">> Local folding")
    folded_circuits = []
    for factor in noise_factors[1:]:
        folded_circuits.append(local_folding(initial_circuit, nb_qubits, factor))

    for i in range(len(folded_circuits)):
        print(folded_circuits[i])

