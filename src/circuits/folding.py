# Module: Folding - repeat gates unitarily to boost noise in the circuit
#         Implements the following methods: global folding, local folding
# Date: 22/11/2023


## == Libraries == ##

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

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

    # print(initial_circuit)
    q_register = QuantumRegister(nb_qubits, name='q')

    folded_circuit = QuantumCircuit(q_register)
    
    circuit_instructions = []
    for circuit_instruction in initial_circuit.data:
        # print("Operation: ", circuit_instruction.operation)
        # print("Qubits: ", circuit_instruction.qubits)
        # print("Cbits: ", circuit_instruction.clbits)
        circuit_instructions.append(circuit_instruction)

    # print(circuit_instructions)

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


