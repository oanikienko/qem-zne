# Zero-noise extrapolation on NISQ devices: benchmarking and some new results 

This project performs the benchmarking of zero-noise extrapolation (ZNE) ([[Cai et al, 2023]](#1), [[Li and Benjamin, 2017]](#2), [[Temme et al, 2017]](#3), [[Majumdar et al, 2023]](#4)) on simulators, snapshots and real devices. The main objectives are:
- Finding the best performance-complexity trade-off for ZNE.
- Determining the best implementation of ZNE on NISQ devices.

To achieve these objectives, this project has led to an implementation of zero-noise extrapolation, named `customZNE`. Its main features are the following:
- Global and local folding to boost the noise in the initial circuit.
- Polynomial and exponential extrapolations to compute the noise-free expectation value.

This implementation uses Python 3.9 and higher, under GNU/Linux.

This project also includes experiments using `qiskitZNE`, the ZNE provided by Qiskit from IBM.

This documentation explains how to create the virtual environment required for this implementation and how to process the data obtained during the project.

## How to create the virtual environment

Steps:
1. Clone this GitHub repository in your working directory, here in `~/virenv/`:
	```bash
	git clone https://github.com/oanikienko/qem-zne.git
	```

2. Create the virtual environment in `~/virenv/`:
	```bash
	python3 -m venv ~/virenv/qem-zne/
	```

3. Go in the directory `qem-zne` and activate the newly created environment, while exporting the path variables:
	```bash
	source ~/virenv/qem-zne/bin/activate && export PYTHONPATH="${PYTHONPATH}:~/virenv/qem-zne/src:~/virenv/qem-zne/src/customZNE"
	```
	Path variables must be exported in order to import `customZNE` modules correctly.

4. Upgrade `pip` and install the necessary libraries:
	```bash
	pip install -U pip 
	pip install numpy matplotlib 
	```

For the next times, only the activation of the environment is needed, using the following command:
```bash
source ~/virenv/qem-zne/bin/activate && export PYTHONPATH="${PYTHONPATH}:~/virenv/qem-zne/src:~/virenv/qem-zne/src/customZNE"
```
Once the environment has been created and activated, data can be processed.

## How to process data

> [!IMPORTANT]
> Please note that Qiskit 1.0.0 has been released since March 31st, 2024. As a consequence, the results cannot be reproduced anymore because this new release is not backwards compatible.
> From now on, only data processing can be performed, using the experiment files from this repository. The following section has been rewritten accordingly.

The data obtained after running the script is stored in `src/data/`, under the name `<experiment_filename>_results.yaml`.


Steps:
1. Activate the environment if you have not already done so:
	```bash
	source ~/virenv/qem-zne/bin/activate && export PYTHONPATH="${PYTHONPATH}:~/virenv/qem-zne/src:~/virenv/qem-zne/src/customZNE"
	```

2. Go into the directory `src` where all the scripts are stored:
	```bash
	cd src/
	```

3. Process the data created with `zne_performing.py`. Two scripts are available:
	1. To plot with linear scale on both axes,  run `data_processing.py`:
		```bash
		python3 data_processing.py data/chosen_ZNE/<experiment_filename>_results.yaml results/path/to/storage/directory/
		```

	2. To plot figures using logarithm scale on the x-axis, run `logarithm_data_processing.py` instead, with the same parameters:
		```bash
		python3 logarithm_data_processing.py data/chosen_ZNE/<experiment_filename>_results.yaml results/path/to/storage/directory/
		```
	Please note that:
	- `chosen_ZNE`is either `customZNE` or `qiskitZNE`.
	- `<experiment_filename>_results.yaml`is one of the files in `data/chosen_ZNE/`.
	- `results/path/to/storage/directory/` is the directory where the figures will be stored after executing the script.

## References

- <a id="1">[Cai et al, 2023]</a> Z. Cai, R. Babbush, S. C. Benjamin, S. Endo, W. J. Huggins, Y. Li, J. R. McClean, and T. E. O’Brien, “Quantum Error Mitigation,” Jun.  2023, first consultation on 12/07/2023. [Online]. Available: [http://arxiv.org/abs/2210.00921](http://arxiv.org/abs/2210.00921).

- <a id="2">[Li and Benjamin, 2017]</a> Y. Li and S. C. Benjamin, “Efficient Variational Quantum Simulator Incorporating Active Error Minimization,” Phys. Rev. X, vol. 7, no. 2, p. 021050, Jun. 2017, first consultation on 27/06/2023. [Online]. Available: [https://link.aps.org/doi/10.1103/PhysRevX.7.021050](https://link.aps.org/doi/10.1103/PhysRevX.7.021050).

- <a id="3">[Temme et al, 2017]</a> K. Temme, S. Bravyi, and J. M. Gambetta, “Error Mitigation for Short-Depth Quantum Circuits,” Phys. Rev. Lett., vol. 119, no. 18, p.  180509, Nov. 2017, first consultation on 30/06/2023. [Online]. Available: [https://link.aps.org/doi/10.1103/PhysRevLett.119.180509](https://link.aps.org/doi/10.1103/PhysRevLett.119.180509).

- <a id="4">[Majumdar et al, 2023]</a> R. Majumdar, P. Rivero, F. Metz, A. Hasan, and D. S. Wang, “Best practices for quantum error mitigation with digital zero-noise extrapolation,” Jul. 2023, first consultation on 18/08/2023. [Online]. Available: [http://arxiv.org/abs/2307.05203](http://arxiv.org/abs/2307.05203).




