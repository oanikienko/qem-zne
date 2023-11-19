# Module: providers
# Author: oanikienko
# Date: 19/11/2023

# == Libraries == #



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


def get_gate_error_rates(provider_backend, gate='cx'):

    gate_error_rates = dict()
    for key in provider_backend.target[gate]:
        #print(key, '- gate error:', fake_backend.target[gate][key].error)
        gate_error_rates[key] = fake_backend.target[gate][key].error

    return gate_error_rates
