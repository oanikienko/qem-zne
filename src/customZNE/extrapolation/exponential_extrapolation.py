# Module: Exponential extrapolation
# Author: oanikienko
# Date: 31/12/2023

## == Libraries == ##

import numpy as np
import scipy
import matplotlib.pyplot as plt

## == Functions == ##

def exponential_from_coefficients(x, coefs):
    # coefs[0] = shift
    # coefs[1] = amplitude
    # coefs[2] = rate

    x = np.array(x)
    return coefs[0]+ coefs[1]*np.exp(-coefs[2]*x)


def exponential_function(x, shift, amplitude, rate): # curve_fit: order of the optimal_coefs = order of the parameters after x
    x = np.array(x)
    return shift+amplitude*np.exp(-rate*x) # ref: GHL+20 (10.1109/qce49297.2020.00045)


def exponential_extrapolation(x, y, standard_deviations, p0=None):
    if p0 == None:
        p0=[2 ** (-i) for i in range(1 * 2 + 1)] # 1 term because mono-exponential extrapolation

    optimal_coefs, covariance_matrix = scipy.optimize.curve_fit(exponential_function, x, y, sigma=standard_deviations, absolute_sigma=True, p0=p0, bounds=([-np.inf] + [-np.inf, 0], np.inf), max_nfev=None)

    return optimal_coefs, covariance_matrix



## == Tests == ##

if __name__ == "__main__":

    x = [0.08239080811833915, 0.7415172730650523, 2.0597702029584792, 4.037149597798618, 6.673655457585467, 9.969287782319052]

    y = [0.73, 0.728, 0.684, 0.576, 0.594, 0.532]

    std_deviations = [np.sqrt(0.46710000000000007), np.sqrt(0.470016), np.sqrt(0.532144), np.sqrt(0.668224), np.sqrt(0.6471640000000001), np.sqrt(0.716976)]

    monoexp_optimal_coefs, monoexp_covariance_matrix = exponential_extrapolation(x, y, std_deviations)
    monoexp_optimal_coefs = [opti_coef.item() for opti_coef in monoexp_optimal_coefs]
    monoexp_y_opti = exponential_from_coefficients(x, monoexp_optimal_coefs)

    plt.scatter(x, y, marker="x")
    plt.plot(x, monoexp_y_opti, label="monoexp_y_opti")
    plt.legend()
    plt.show()
