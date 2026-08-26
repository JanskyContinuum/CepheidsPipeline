import numpy as np


def extract_lightcurve_parameters(df_clean):
    """
    Extracts basic physical parameters from the cleaned light curve.
    Uses intensity-mean magnitude, the standard for P-L relations.
    """
    if df_clean is None or len(df_clean) == 0:
        return np.nan, np.nan, np.nan, 0, np.nan

    # mag to flux
    fluxes = 10 ** (-0.4 * df_clean['mag'])
    mean_flux = np.mean(fluxes)

    # flux to mag
    intensity_mean_mag = -2.5 * np.log10(mean_flux)

    # amplitude
    amplitude = df_clean['mag'].max() - df_clean['mag'].min()

    # RMS
    rms = np.std(df_clean['mag'])
    n_obs = len(df_clean)

    # Mean photometric error
    mean_err = np.mean(df_clean['err'])

    return intensity_mean_mag, amplitude, rms, n_obs, mean_err