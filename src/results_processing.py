    #print(">> Plotting the data with variances...")
    #plt.rcParams["figure.figsize"] = (5,3.5)
    #plt.grid(which='major',axis='both')

    #plt.errorbar([0, noise_factors[-1]],[ideal_expectation_values[0], ideal_expectation_values[-1]], [ideal_std_deviations[0], ideal_std_deviations[-1]], linestyle="--", label=f"Ideal", color="#000000")
    #plt.scatter(0, mitigated_value, label=f"Mitigated", marker="x", color="#785ef0")
    #plt.errorbar(noise_factors, noisy_expectation_values, noisy_std_deviations, linestyle='None', marker='.', capsize=3, label=f"Unmitigated", color="#dc267f")
    #plt.title("Zero-noise extrapolation - Global folding")
    #plt.xlabel("Noise factors")
    #plt.ylabel(f"Expectation Value ($\langle {observable.paulis[0]} \\rangle$)")
    #plt.legend()
    #plt.show()

    #plt.plot([0, noise_factors[-1]],[ideal_expectation_values[0], ideal_expectation_values[-1]], linestyle="--", label=f"Ideal", color="#000000")
    #plt.scatter(0, mitigated_value, label=f"Mitigated", marker="x", color="#785ef0")
    #plt.plot(noise_factors, noisy_expectation_values, linestyle='None', marker='.', label=f"Unmitigated", color="#dc267f")
    #plt.title("Zero-noise extrapolation - Global folding")
    #plt.xlabel("Noise factors")
    #plt.ylabel(f"Expectation Value ($\langle {observable.paulis[0]} \\rangle$)")
    #plt.legend()
    #plt.show()



