# Script: Utilities for time measurement of the jobs on IBM Quantum
# Author: oanikienko
# Date: 21/01/2024

## === Libraries === ##

from datetime import datetime, timedelta

from qiskit_ibm_runtime import QiskitRuntimeService, Options, Session
from qiskit_ibm_runtime import Estimator as IBMQEstimator

## === Functions === ##

def measure_job_execution_time(job):
    start_timestamp = job.metrics()["timestamps"]["created"].replace("T", " ").replace("Z", "")
    start_datetime = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S.%f")

    stop_timestamp = job.metrics()["timestamps"]["finished"].replace("T", " ").replace("Z", "")
    stop_datetime = datetime.strptime(stop_timestamp, "%Y-%m-%d %H:%M:%S.%f")

    return stop_datetime - start_datetime, job.metrics()['usage']['quantum_seconds']


