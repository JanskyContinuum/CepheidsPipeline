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

# Ensure Python can find the 'src' module regardless of the working directory
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# PIPELINE MODULES

from src.data import download_ogle_data
from src.cleaning import ingest_and_clean
from src.period import find_period
from src.parameters import extract_lightcurve_parameters


def run_pl_pipeline(num_stars=100):
    results = []
    print(f"Starting processing of {num_stars} Cepheids from LMC...")

    # Ensure output directory exists
    os.makedirs(os.path.join(RESULTS_DIR, "pl_relation"), exist_ok=True)

    for star_id in range(1, num_stars + 1):
        # 1. Download
        filepath = download_ogle_data(star_id, download_dir=DATA_DIR)
        if not filepath:
            continue

        # 2. Clean
        df_clean = ingest_and_clean(filepath)

        # Skip stars with insufficient data points
        if len(df_clean) < 50:
            print(f"Skipping CEP-{star_id:04d} (insufficient data).")
            continue

        # 3. Find Period
        best_period = find_period(df_clean, min_period=0.10)[0]

        # 4. Extract Parameters
        mean_mag, amplitude, rms, n_obs = extract_lightcurve_parameters(df_clean)

        # 5. Store Results
        results.append({
            'ID': f'OGLE-LMC-CEP-{star_id:04d}',
            'Period': best_period,
            'logP': np.log10(best_period),
            'Mean_Mag': mean_mag,
            'Amplitude': amplitude,
            'RMS': rms,
            'N_obs': n_obs
        })

        # Small delay to respect OGLE FTP servers
        time.sleep(0.1)

        # Save data
    df_results = pd.DataFrame(results)

    csv_path = os.path.join(RESULTS_DIR, "pl_relation/cepheid_parameters.csv")
    df_results.to_csv(csv_path, index=False)
    print(f"\nBatch processing complete. Data saved to {csv_path}")

    return df_results


def plot_pl_relation(df_results):
    """
    Plots the Period-Luminosity relation and fits a linear regression model.
    """
    print("Generating Period-Luminosity (Leavitt Law) plot...")

    logP = df_results['logP']
    mag = df_results['Mean_Mag']

    # Perform linear regression: m = a * log(P) + b
    slope, intercept, r_value, p_value, std_err = linregress(logP, mag)

    # Generate line points
    x_fit = np.linspace(logP.min(), logP.max(), 100)
    y_fit = slope * x_fit + intercept

    plt.figure(figsize=(10, 6))

    # Plot individual stars
    plt.scatter(logP, mag, c='blue', alpha=0.6, edgecolors='k', s=30, label='LMC Cepheids')

    # Plot regression line
    equation_text = f"Fit: $m = {slope:.3f} \cdot \log_{{10}}(P) + {intercept:.3f}$"
    plt.plot(x_fit, y_fit, color='red', linewidth=2, label=equation_text)


    plt.gca().invert_yaxis()  # Brighter stars -lower magnitude)
    plt.xlabel('$\log_{10}(Period)$ [days]', fontsize=12)
    plt.ylabel('Mean I-band Magnitude', fontsize=12)
    plt.title('Period-Luminosity Relation for LMC Cepheids (OGLE-IV Data)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(fontsize=11)

    plot_path = os.path.join(RESULTS_DIR, "pl_relation/pl_relation_fit.png")

    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved successfully to {plot_path}")
    plt.show()


if __name__ == "__main__":
    # Run the pipeline for the first 100 Cepheids
    results_dataframe = run_pl_pipeline(num_stars=100)

    # Generate the plot
    if not results_dataframe.empty:
        plot_pl_relation(results_dataframe)
