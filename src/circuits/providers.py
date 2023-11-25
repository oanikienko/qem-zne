# Module: providers
# Author: oanikienko
# Date: 19/11/2023

# == Libraries == #

# from utils import configuration
from pathlib import Path
from circuits import initial_circuits as init
from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit.providers.fake_provider import FakeManilaV2, FakeNairobiV2
import pprint

# == Functions == #

def get_backend_info(provider_backend):
    ## TODO à mettre à jour (noms de variables, etc.) lors du choix des providers

    backend_info = {
        'name': provider_backend.name,
        'version': provider_backend.backend_version,
        'online_date': provider_backend.online_date,
        'syst_time_resolution_input_signals': provider_backend.dt,
        'syst_time_resolution_output_signals': provider_backend.dtm,
        'max_circuits_per_job': provider_backend.max_circuits,
        'num_qubits': provider_backend.num_qubits,
        'coupling_map': provider_backend.coupling_map,
        'operation_names': provider_backend.operation_names,
        'instruction_durations': provider_backend.instruction_durations,
        'instruction_schedule_map': provider_backend.instruction_schedule_map,
        'target': provider_backend.target
    }

    return backend_info

def print_backend_info(provider_info):

    print("Name: ", provider_info['name'])
    print("Version: ", provider_info['version'])
    print("Online date: ", provider_info['online_date'])
    print("Max circuits per job: ", provider_info['max_circuits_per_job'])
    print("Number of qubits: ", provider_info['num_qubits'])

    print("System time resolution:")
    print("\tInput signals: ", provider_info['syst_time_resolution_input_signals'])
    print("\tOutput signals: ", provider_info['syst_time_resolution_output_signals'])

    print("Coupling map:")
    provider_info['coupling_map'].draw()

    print("Operations names: ", provider_info['operation_names'])

    print("Target:")
    for gate in provider_info['target'].keys():
        print("\t", gate)
        for qbits in provider_info['target'][gate].keys():
            if provider_info['target'][gate][qbits] != None and provider_info['target'][gate][qbits] != None:
                print("\t\tQubit(s) {0}: duration={1}, error={2}".format(qbits, provider_info['target'][gate][qbits].duration, provider_info['target'][gate][qbits].error))
            else:
                print("\t\tQubit(s) {0}: duration=None, error=None".format(qbits))

        # print("\t\t", provider_info['target'][gate])
        # print("{0}: {1}".format(provider_info['target'][target_key], provider_info['target'][target_key]))



def get_gate_errors(provider_backend):

    gate_errors = dict()

    for gate in provider_backend.target.keys():
        # print("\t", gate)
        gate_errors[gate] = dict()
        for qbits in provider_backend.target[gate].keys():
            if provider_backend.target[gate][qbits] != None and provider_backend.target[gate][qbits] != None:
                # print("\t\tQubit(s) {0}: duration={1}, error={2}".format(qbits, provider_backend.target[gate][qbits].duration, provider_backend.target[gate][qbits].error))
                gate_errors[gate][qbits] = provider_backend.target[gate][qbits].error
            else:
                # print("\t\tQubit(s) {0}: duration=None, error=None".format(qbits))
                gate_errors[gate][qbits] = None
    
    return gate_errors


def calculate_error_rate(circuit, provider_backend, noise_factor):

    # Get gates in the circuit
    instructions = dict()
    for circuit_instruction in circuit.data:
        # print("Operation: ", circuit_instruction.operation)
        # print("Qubits: ", circuit_instruction.qubits)
        # print("\tFind qubit: ", [circuit.find_bit(qubit) for qubit in circuit_instruction.qubits])
        # print("\tIndex: ", tuple([circuit.find_bit(qubit).index for qubit in circuit_instruction.qubits]))
        # print("\tRegister: ", [circuit.find_bit(qubit).registers for qubit in circuit_instruction.qubits])
        # print("Cbits: ", circuit_instruction.clbits)

        gate = circuit_instruction.operation.name
        indexes = tuple([circuit.find_bit(qubit).index for qubit in circuit_instruction.qubits])

        if not gate in instructions:
            instructions[gate] = []

        l = instructions[gate]
        l.append(indexes)
        instructions[gate] = l
        
    # Get the error rate for each gate for the provider_backend
    gate_errors = get_gate_errors(provider_backend)


    # Compute the error rate of the circuit
    circuit_error_rate = 0
    for gate in instructions:
        for qubits in instructions[gate]:
            circuit_error_rate += noise_factor*gate_errors[gate][qubits]

    return circuit_error_rate
    

## == Tests == ##

if __name__ == "__main__":

    # print(">> Defining the .ini file to use...")
    # filename = "../credentials.ini"

    # config = configuration.load_config(filename)

    # print(">> Connecting to IBM Cloud...")
    # service = QiskitRuntimeService(channel=config["ibmq.cloud"]["channel"], token=config["ibmq.cloud"]["API_key"], instance=config["ibmq.cloud"]["instance"])

    print(">> Information about different providers")

    fake_Manila = FakeManilaV2()

    Manila_info = get_backend_info(fake_Manila)
    print_backend_info(Manila_info)
    Manila_gate_errors = get_gate_errors(fake_Manila)
    pp = pprint.PrettyPrinter(depth=5)
    pp.pprint(Manila_gate_errors)

    
    fake_Nairobi = FakeNairobiV2()

    Nairobi_info = get_backend_info(fake_Nairobi)
    print_backend_info(Nairobi_info)
    Nairobi_gate_errors = get_gate_errors(fake_Nairobi)
    pp = pprint.PrettyPrinter(depth=5)
    pp.pprint(Nairobi_gate_errors)


    print(">> Circuit error rate with FakeNairobiV2")

    nb_qubits = 4
    noise_factor = 1

    initial_circuit = init.build_initial_circuit(nb_qubits, init.U_4qubits)
    print(initial_circuit)

    initial_fault_rate = calculate_error_rate(initial_circuit, fake_Nairobi, noise_factor)
    print("FakeNairobi - Circuit fault rate: ", initial_fault_rate)
