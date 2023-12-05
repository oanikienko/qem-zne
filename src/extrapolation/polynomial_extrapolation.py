# Module: Polynomial extrapolation
# Author: oanikienko
# Date: 17/11/2023

"""
This module contains the functions relative to the polynomial extrapolation.
"""

## == Libraries == ##

import numpy as np
import scipy

## == Functions == ##

def polynomial_function(x, *coefs):
    x = np.array(x)
    return sum(c * (x**i) for i, c in enumerate(coefs))

def polynomial_extrapolation(polynomial_degree, noise_factors, noisy_expectation_values, standard_deviations, p0=None):
    # p0: initial guess for the parameters (length polynomial_degree+1) => random values? Only 0s? only 1s?
    if p0 == None:
        p0 = np.zeros(polynomial_degree+1)

    optimal_coefs, covariance_matrix = scipy.optimize.curve_fit(polynomial_function, noise_factors, noisy_expectation_values, sigma=standard_deviations, absolute_sigma=True, p0=p0)

    return optimal_coefs, covariance_matrix

