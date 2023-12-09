# Module: providers and backends
# Author: oanikienko
# Date: 19/11/2023

# == Libraries == #

# from utils import configuration
from pathlib import Path
from circuits import initial_circuits as init
from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit.providers.fake_provider import FakeProvider, FakeProviderForBackendV2, FakeManilaV2, FakeNairobiV2
import pprint

# == Functions == #

def get_backend_info(backend):

    backend_info = {
        'name': backend.name,
        'version': backend.backend_version,
        'online_date': backend.online_date,
        'syst_time_resolution_input_signals': backend.dt,
        'syst_time_resolution_output_signals': backend.dtm,
        'max_circuits_per_job': backend.max_circuits,
        'num_qubits': backend.num_qubits,
        'coupling_map': backend.coupling_map,
        'operation_names': backend.operation_names,
        'instruction_durations': backend.instruction_durations,
        'instruction_schedule_map': backend.instruction_schedule_map,
        'target': backend.target
    }

    return backend_info

def print_backend_info(backend_info):

    print("Name: ", backend_info['name'])
    print("Version: ", backend_info['version'])
    print("Online date: ", backend_info['online_date'])
    print("Max circuits per job: ", backend_info['max_circuits_per_job'])
    print("Number of qubits: ", backend_info['num_qubits'])

    print("System time resolution:")
    print("\tInput signals: ", backend_info['syst_time_resolution_input_signals'])
    print("\tOutput signals: ", backend_info['syst_time_resolution_output_signals'])

    print("Coupling map:")
    backend_info['coupling_map'].draw()

    print("Operations names: ", backend_info['operation_names'])

    print("Target:")
    for gate in backend_info['target'].keys():
        print("\t", gate)
        for qbits in backend_info['target'][gate].keys():
            if backend_info['target'][gate][qbits] != None and backend_info['target'][gate][qbits] != None:
                print("\t\tQubit(s) {0}: duration={1}, error={2}".format(qbits, backend_info['target'][gate][qbits].duration, backend_info['target'][gate][qbits].error))
            else:
                print("\t\tQubit(s) {0}: duration=None, error=None".format(qbits))

        # print("\t\t", backend_info['target'][gate])
        # print("{0}: {1}".format(backend_info['target'][target_key], backend_info['target'][target_key]))


def get_operations_with_error_rates(backend):

    operations = []

    for gate in backend.target.keys():
        for qbits in backend.target[gate].keys():
            if backend.target[gate][qbits] != None and backend.target[gate][qbits] != None:
                operations.append((gate, qbits))

    return operations


def get_gate_errors(backend):

    gate_errors = dict()

    for gate in backend.target.keys():
        # print("\t", gate)
        gate_errors[gate] = dict()
        for qbits in backend.target[gate].keys():
            if backend.target[gate][qbits] != None and backend.target[gate][qbits] != None:
                # print("\t\tQubit(s) {0}: duration={1}, error={2}".format(qbits, backend.target[gate][qbits].duration, backend.target[gate][qbits].error))
                gate_errors[gate][qbits] = backend.target[gate][qbits].error
            else:
                # print("\t\tQubit(s) {0}: duration=None, error=None".format(qbits))
                gate_errors[gate][qbits] = None
    
    return gate_errors


def calculate_error_rate(circuit, backend, noise_factor):

    # Get gates in the circuit
    instructions = dict()
    for circuit_instruction in circuit.data:

        gate = circuit_instruction.operation.name
        indexes = tuple([circuit.find_bit(qubit).index for qubit in circuit_instruction.qubits])

        if not gate in instructions:
            instructions[gate] = []

        l = instructions[gate]
        l.append(indexes)
        instructions[gate] = l
        
    # Get the error rate for each gate for the backend
    gate_errors = get_gate_errors(backend)


    # Compute the error rate of the circuit
    circuit_error_rate = 0
    for gate in instructions:
        for qubits in instructions[gate]:
            circuit_error_rate += noise_factor*gate_errors[gate][qubits]

    return circuit_error_rate

def search_backend(provider, searched_backend_name):

    searched_backend = None

    for backend in provider.backends():
        if backend.name == searched_backend_name:
            searched_backend = backend

    return searched_backend


def get_backends(provider, backends_names):

    # Returns a list of backends for the given provider if the backend is found among the provided backends
    return [search_backend(provider, name) for name in backends_names if search_backend(provider, name) != None]


def select_backends_for_circuit(provider, circuit):

    selected_backends = []
    circuit_gates = dict()
    backends_gates = dict()

    # 1) Getting the backends for the provider
    backends = provider.backends()
    
    # 2) Getting the existing gates in the circuit
    for circuit_instruction in circuit.data:
        # print("Operation: ", circuit_instruction.operation)
        # print("Qubits: ", circuit_instruction.qubits)
        # print("\tFind qubit: ", [circuit.find_bit(qubit) for qubit in circuit_instruction.qubits])
        # print("\tIndex: ", tuple([circuit.find_bit(qubit).index for qubit in circuit_instruction.qubits]))
        # print("\tRegister: ", [circuit.find_bit(qubit).registers for qubit in circuit_instruction.qubits])
        # print("Cbits: ", circuit_instruction.clbits)
        gate = circuit_instruction.operation.name
        indexes = tuple([circuit.find_bit(qubit).index for qubit in circuit_instruction.qubits])

        if not gate in circuit_gates:
            circuit_gates[gate] = []

        l = circuit_gates[gate]
        l.append(indexes)
        circuit_gates[gate] = l

    # 3) Getting the gates with known error rates for all backends
    for backend in backends:
        backends_gates[backend.name] = get_gate_errors(backend)

    # 4) Selecting the backends for which the gates with known error rates are the ones in the circuit
    for backend_name in backends_gates.keys():
        gates = backends_gates[backend_name]
        for gate in gates.keys():
            if gate in circuit_gates.keys():
                if (all(qubits in gates[gate].keys() for qubits in circuit_gates[gate])):
                    selected_backends.append(backend_name)

    return selected_backends

## == Tests == ##

if __name__ == "__main__":

    # print(">> Defining the .ini file to use...")
    # filename = "../credentials.ini"

    # config = configuration.load_config(filename)

    # print(">> Connecting to IBM Cloud...")
    # service = QiskitRuntimeService(channel=config["ibmq.cloud"]["channel"], token=config["ibmq.cloud"]["API_key"], instance=config["ibmq.cloud"]["instance"])

    print(">> Information about different backends")

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


    print(">> Search of backends provided by a provider (FakeProviderV2 only)")

    fake_provider_V2 = FakeProviderForBackendV2()

    found_backend = search_backend(fake_provider_V2, "fake_manila")
    print(found_backend)

    backends_names = ["fake_manila", "fake_almaden", "fake_armonk", "fake_athens", "fake_auckland", "fake_belem"]
    backends = get_backends(fake_provider_V2, backends_names)
    print(backends)
