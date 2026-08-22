from astropy.timeseries import LombScargle
import numpy as np
from scipy.signal import find_peaks


def find_period(df_clean, min_period=0.10, max_period=100.0):
    """
    Analyzes the time series using the Lomb-Scargle periodogram
    to find the most likely period of pulsation.

    Parameters:
    - df_clean: DataFrame from Phase A (must contain HJD, mag, err)
    - min_period, max_period: Search boundaries in days (Cepheids typically range 1-100 days)
    """

    time = df_clean['HJD'].values
    mag = df_clean['mag'].values
    err = df_clean['err'].values

    ls = LombScargle(time, mag, err)

    min_freq = 1.0 / max_period
    max_freq = 1.0 / min_period

    frequency, power = ls.autopower(minimum_frequency=min_freq, maximum_frequency=max_freq)

    # find peaks
    peak_indices, _ = find_peaks(power, distance=50)

    # sort them according to power
    sorted_peak_indices = peak_indices[np.argsort(power[peak_indices])[::-1]]

    # choose 5 best
    top_indices = sorted_peak_indices[:5]

    best_frequencies = frequency[top_indices]
    best_periods = 1.0 / best_frequencies
    best_powers = power[top_indices]

    primary_period = best_periods[0]

    return primary_period, frequency, power, best_periods, best_powers

