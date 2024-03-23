# Module: Functions for loading and storing data (CSV format)
# Author: oanikienko
# Date: 05/12/2023


## == Libraries == ##

import numpy as np
import yaml
from pathlib import Path

## == Functions == ##

def load_data(working_directory, filename):

    base_path = Path(working_directory)
    file_path = (base_path / filename).resolve()
    
    with open(file_path, 'r') as yamlfile:
        data = yaml.load(yamlfile, Loader = yaml.FullLoader)

    return data


def store_data(data, working_directory, filename):

    base_path = Path(working_directory)
    file_path = (base_path / filename).resolve()

    with open(file_path, 'w') as yamlfile:
        result = yaml.dump(data, yamlfile, sort_keys=False)
        

    
## == Tests == ##

if __name__ == "__main__":

    print(">> Defining a filename...")
    filename = "./test.yaml"

    print(">> Creating data to store...")
    data = [
            {"noise_factor": 3, 
             "results": {"expectation_value": 0.654, "variance": 0.572}
            }, 
            {"noise_factor": 5, 
             "results": {"expectation_value": 0.546, "variance": 0.702}
            },
            {"noise_factor": 7, 
             "results": {"expectation_value": 0.536, "variance": 0.713}
            },
           ]

    print(">> Before storing data:")
    print(data)

    store_data(data, ".", filename)

    data = load_data(".", filename)

    print(">> After loading data:")
    print(data)


