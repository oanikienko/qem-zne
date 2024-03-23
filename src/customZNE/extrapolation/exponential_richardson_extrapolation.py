# Module: Exponential-Richardson extrapolation
# Author: oanikienko
# Date: 31/12/2023

## == Libraries == ##

import numpy as np
import scipy
import math
import matplotlib.pyplot as plt

## == Functions == ##

def exponential_richardson_extrapolation(fault_rates, noisy_expectation_values):
        
    fault_rates = np.array(fault_rates)
    noisy_expectation_values = np.array(noisy_expectation_values)
    
    mitigated_value = 0
    A = 0
    
    for i in range(len(fault_rates)):
        gamma_i = 1
        for k in range(len(fault_rates)):
            if k != i:
                gamma_i *= fault_rates[k]/(fault_rates[k]-fault_rates[i])
        
        alpha_i = gamma_i * np.exp(fault_rates[i])
        
        A += alpha_i

        mitigated_value += alpha_i*noisy_expectation_values[i]
    
    return mitigated_value/A


## == Tests == ##

if __name__ == "__main__":

    fault_rates = [0.08239080811833915, 0.7415172730650523, 2.0597702029584792, 4.037149597798618, 6.673655457585467, 9.969287782319052]

    noisy_expectation_values = [0.73, 0.728, 0.684, 0.576, 0.594, 0.532]
    
    noiseless_expectation_value = exponential_richardson_extrapolation(fault_rates, noisy_expectation_values)

    plt.scatter(fault_rates, noisy_expectation_values, marker="x")

    plt.plot(0, noiseless_expectation_value, marker=".", label="exponential-richardson")

    plt.legend()
    plt.show()

