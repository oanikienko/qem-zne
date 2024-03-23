# Zero-noise extrapolation on NISQ devices: benchmarking and some new results 

This project performs the benchmarking of zero-noise extrapolation (ZNE) ([[1]](#1), [[2]](#2), [[3]](#3), [[4]](#4)) on simulators, snapshots and real devices. The main objectives are:
- Finding the best performance-complexity trade-off for ZNE.
- Determining the best implementation of ZNE on NISQ devices.

To achieve these objectives, this project has led to an implementation of zero-noise extrapolation, named `customZNE`. Its main features are the following:
- Global and local folding to boost the noise in the initial circuit.
- Polynomial and exponential extrapolations to compute the noise-free expectation value.
This implementation uses Python 3.9 and higher, under GNU/Linux.

This project also includes experiments using `qiskitZNE`, the ZNE provided by Qiskit from IBM.

This documentation explains how to create the virtual environment required for this implementation and how to reproduce the results obtained during the project.

## How to create the virtual environment

Firstly, the virtual environment needs to be created from the `requirements.txt` file. It contains all the packages used by `customZNE` and the other scripts of the project.

Steps:
1. Clone this GitHub repository in your working directory, here `~/virenv/`:
```bash
~/virenv$ git clone https://github.com/oanikienko/qem-zne.git
```
2. Create the virtual environment:
```bash
~/virenv$ python3 -m venv qem-zne/
```
3. Go in the directory `qem-zne` and activate the newly created environment, while exporting the path variables:
```bash
~/virenv/qem-zne$ source ./bin/activate && export PYTHONPATH="${PYTHONPATH}:~/virenv/qem-zne/src:~/virenv/qem-zne/src/customZNE"
```
The path variables need to be exported in order to import correctly the modules of `customZNE`.
4. Upgrade `pip` and install the dependencies using `requirements.txt`:
```bash
(qem-zne) ~/virenv/qem-zne$ pip install -U pip 
(qem-zne) ~/virenv/qem-zne$ pip install -r requirements.txt 
```

For the next times, only the activation of the environment is needed, using the following command:
```bash
~/virenv/qem-zne$ source ./bin/activate && export PYTHONPATH="${PYTHONPATH}:~/virenv/qem-zne/src:~/virenv/qem-zne/src/customZNE"
```

Once the environment has been created and activated, the results can be reproduced.

## How to reproduce the results

To reproduct the results, an IBM account on [https://quantum.ibm.com/](https://quantum.ibm.com/) is required. After creating the account, the API token can be found in the [profile settings](https://quantum.ibm.com/account).

The reproduction of the results includes the following steps:
1. Create the credentials file.
2. Performing ZNE on an experiments file, using the script `zne_performing.py`.
3. Processing the obtained data, using the script `data_processing.py`.

### Credentials file

The file containing the credentials for IBMQ is called `credentials.ini` and has to be stored in `src/`, so that the path is `./qem-zne/src/credentials.ini`. 

Its content is as follows: 
```ini
[ibm.quantum]
channel = ibm_quantum
api_token = <api_token>
instance = ibm-q/open/main
```
`<api_token>` must be replaced by your API key, which can be found in your IBM account settings.


### ZNE performing

After creating the `credentials.ini` file, `customZNE` can be performed on an experiment file. This kind of files is stored in `src/experiments/`. 

The typical command to perform ZNE is as follows:
```bash
(qem-zne) ~/virenv/qem-zne$ python3 zne_performing.py experiments/<experiment_filename>.yaml
```

The data obtained after running the script is stored in `src/data/`, under the name `<experiment_filename>_results.yaml`.

### Data processing

To process the data created with `zne_performing.py`, the following command has to be executed:
```bash
(qem-zne) ~/virenv/qem-zne$ python3 data_processing.py data/<experiment_filename>_results.yaml results/path/to/storage/directory/
```
The figures will be created from the file, and stored in the directory passed as parameter.

To plot figures using logarithm scale on the x-axis, the command uses the script `logarithm_data_processing.py` as follows:
```bash
(qem-zne) ~/virenv/qem-zne$ python3 logarithm_data_processing.py data/<experiment_filename>_results.yaml results/path/to/storage/directory/
```

## References
<a id="1">[1]</a> Z. Cai, R. Babbush, S. C. Benjamin, S. Endo, W. J. Huggins, Y. Li, J. R. McClean, and T. E. O’Brien, “Quantum Error Mitigation,” Jun.  2023, first consultation on 12/07/2023. [Online]. Available: [http://arxiv.org/abs/2210.00921](http://arxiv.org/abs/2210.00921).

<a id="2">[2]</a> Y. Li and S. C. Benjamin, “Efficient Variational Quantum Simulator Incorporating Active Error Minimization,” Phys. Rev. X, vol. 7, no. 2, p. 021050, Jun. 2017, first consultation on 27/06/2023. [Online]. Available: [https://link.aps.org/doi/10.1103/PhysRevX.7.021050](https://link.aps.org/doi/10.1103/PhysRevX.7.021050).

<a id="3">[3]</a> K. Temme, S. Bravyi, and J. M. Gambetta, “Error Mitigation for Short-Depth Quantum Circuits,” Phys. Rev. Lett., vol. 119, no. 18, p.  180509, Nov. 2017, first consultation on 30/06/2023. [Online]. Available: [https://link.aps.org/doi/10.1103/PhysRevLett.119.180509](https://link.aps.org/doi/10.1103/PhysRevLett.119.180509).

<a id="4">[4]</a> R. Majumdar, P. Rivero, F. Metz, A. Hasan, and D. S. Wang, “Best practices for quantum error mitigation with digital zero-noise extrapolation,” Jul. 2023, first consultation on 18/08/2023. [Online]. Available: [http://arxiv.org/abs/2307.05203](http://arxiv.org/abs/2307.05203).



