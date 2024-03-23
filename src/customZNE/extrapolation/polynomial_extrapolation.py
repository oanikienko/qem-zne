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

def polynomial_from_coefficients(x, coefs):
    degree = len(coefs)
    y = 0
    for i in range(degree):
        y += coefs[i]*x**i
    return y

def polynomial_function(x, *coefs):
    x = np.array(x)
    return sum(c * (x**i) for i, c in enumerate(coefs))

def polynomial_extrapolation(polynomial_degree, x, y, standard_deviations, p0=None):
    if p0 == None:
        p0 = np.zeros(polynomial_degree+1)

    optimal_coefs, covariance_matrix = scipy.optimize.curve_fit(polynomial_function, x, y, sigma=standard_deviations, absolute_sigma=True, p0=p0)

    return optimal_coefs, covariance_matrix

