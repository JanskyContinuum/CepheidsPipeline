import os
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress

# PATH CONFIGURATION
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.data import download_ogle_data
from src.cleaning import ingest_and_clean
from src.period import find_period
from src.parameters import extract_lightcurve_parameters

# Extinction-to-reddening ratio for LMC (V and I bands)
R_I = 1.55


def run_multiband_pl_pipeline(num_stars=100):
    results = []
    print(f"Starting multi-band processing of {num_stars} Cepheids from LMC...")
    os.makedirs(os.path.join(RESULTS_DIR, "pl_relation"), exist_ok=True)

    for star_id in range(1, num_stars + 1):
        # 1. Download data for both bands
        filepath_I = download_ogle_data(star_id, band="I", download_dir=DATA_DIR)
        filepath_V = download_ogle_data(star_id, band="V", download_dir=DATA_DIR)

        if not filepath_I or not filepath_V:
            continue

        # 2. Clean
        df_clean_I = ingest_and_clean(filepath_I)
        df_clean_V = ingest_and_clean(filepath_V)

        # Skip stars with insufficient data points (V typically has fewer points)
        if len(df_clean_I) < 50 or len(df_clean_V) < 15:
            print(f"Skipping CEP-{star_id:04d} (insufficient data).")
            continue

        # 3. Find Period (using I-band for maximum stability, enforcing it for V)
        best_period = find_period(df_clean_I, min_period=0.10)[0]

        # 4. Extract Parameters
        I_mean, I_amp, I_rms, I_n_obs, I_err = extract_lightcurve_parameters(df_clean_I)
        V_mean, V_amp, V_rms, V_n_obs, V_err = extract_lightcurve_parameters(df_clean_V)

        # 5. Calculate Wesenheit Index (W_I = I - R_I * (V - I))
        W_I = I_mean - R_I * (V_mean - I_mean)

        # Error propagation for W_I: Var(W_I) = (1+R)^2 * Var(I) + R^2 * Var(V)
        W_I_err = np.sqrt(((1 + R_I) ** 2) * (I_err ** 2) + (R_I ** 2) * (V_err ** 2))

        # 6. Store Results
        results.append({
            'ID': f'OGLE-LMC-CEP-{star_id:04d}',
            'Period': best_period,
            'logP': np.log10(best_period),
            'V_mean': V_mean,
            'I_mean': I_mean,
            'V_err': V_err,
            'I_err': I_err,
            'W_I': W_I,
            'W_I_err': W_I_err,
            'V_amp': V_amp,
            'I_amp': I_amp,
            'V_rms': V_rms,
            'I_rms': I_rms,
            'V_n_obs': V_n_obs,
            'I_n_obs': I_n_obs
        })
        time.sleep(0.1)

    df_results = pd.DataFrame(results)
    csv_path = os.path.join(RESULTS_DIR, "pl_relation/cepheid_multiband_parameters.csv")
    df_results.to_csv(csv_path, index=False)
    print(f"\nBatch processing complete. Data saved to {csv_path}")
    return df_results


def plot_multiband_pl_relation(df_results):
    """
    Plots the Period-Luminosity relation for V, I, and Wesenheit W_I.
    """
    print("Generating Multi-Band Period-Luminosity (Leavitt Law) comparison plot...")

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True)
    logP = df_results['logP']

    plot_configs = [
        ('V_mean', 'Mean V-band Magnitude', axes[0], 'green'),
        ('I_mean', 'Mean I-band Magnitude', axes[1], 'red'),
        ('W_I', 'Wesenheit Index ($W_I$)', axes[2], 'blue')
    ]

    for mag_col, label, ax, color in plot_configs:
        mag = df_results[mag_col]
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = linregress(logP, mag)
        x_fit = np.linspace(logP.min(), logP.max(), 100)
        y_fit = slope * x_fit + intercept

        ax.scatter(logP, mag, c=color, alpha=0.5, edgecolors='k', s=30, label='LMC Cepheids')
        equation_text = f"Fit: $m = {slope:.3f} \cdot \log_{{10}}(P) + {intercept:.3f}$\nScatter (RMS): {np.std(mag - (slope * logP + intercept)):.3f} mag"

        ax.plot(x_fit, y_fit, color='black', linewidth=2, label=equation_text)
        ax.invert_yaxis()
        ax.set_xlabel('$\log_{10}(Period)$ [days]', fontsize=12)
        ax.set_ylabel(label, fontsize=12)
        ax.set_title(f'P-L Relation: {label}', fontsize=14)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(fontsize=10)

    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, "pl_relation/pl_relation_multiband_scatter.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Comparison plot saved successfully to {plot_path}")


if __name__ == "__main__":
    results_dataframe = run_multiband_pl_pipeline(num_stars=100)
    if not results_dataframe.empty:
        plot_multiband_pl_relation(results_dataframe)