import os
import sys
import pandas as pd
import matplotlib.pyplot as plt


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


def fold_light_curve(df_clean, best_period):
    """
    Folds the time-series data into a single pulsation phase [0, 1]
    using the best period found in Phase B.
    """

    t0 = df_clean['HJD'].min()

    # Phase = (Time - T0) / Period
    df_clean['phase'] = ((df_clean['HJD'] - t0) / best_period) % 1.0

    # Duplicate the data to show two full cycles [0.0, 2.0].
    df_extended = df_clean.copy()
    df_extended['phase'] = df_extended['phase'] + 1.0

    # Combine
    phased = pd.concat([df_clean, df_extended], ignore_index=True)

    return phased

def generate_multipanel_plot(df_clean, df_phased, primary_period, frequency, power, top_periods, top_powers, star_id):

    fig, axes = plt.subplots(3, 1, figsize=(12, 12), gridspec_kw={'hspace': 0.4})

    # Top Panel: Raw Time Series (Time vs Mag)
    ax1 = axes[0]
    ax1.errorbar(df_clean['HJD'], df_clean['mag'], yerr=df_clean['err'],
                 fmt='.', color='gray', alpha=0.5, markersize=3)
    ax1.invert_yaxis()
    ax1.set_xlabel('Time [HJD]')
    ax1.set_ylabel('Magnitude [mag]')
    ax1.set_title(f'Cleaned Time Series - {star_id}')

    # Middle Panel: Periodogram (Period vs Power)
    ax2 = axes[1]
    periods_to_plot = 1.0 / frequency
    ax2.plot(periods_to_plot, power, color='purple', linewidth=1)

    # Top N peaks
    colors = ['red', 'orange', 'green', 'cyan', 'blue']
    for i in range(len(top_periods)):
        ax2.axvline(x=top_periods[i], color=colors[i % len(colors)], linestyle='--', alpha=0.7,
                    label=f'Rank {i + 1}: P = {top_periods[i]:.4f} d')

        ax2.scatter(top_periods[i], top_powers[i], color=colors[i % len(colors)], zorder=5)

    ax2.set_xlabel('Period [days]')
    ax2.set_ylabel('Lomb-Scargle Power')
    ax2.set_title('Frequency Analysis with Top Peaks Marked')
    ax2.set_xlim(0.1, 15)
    ax2.legend(loc='upper right', fontsize='small')

    # Bottom Panel: Phased Light Curve (Phase vs Mag)

    ax3 = axes[2]
    ax3.errorbar(df_phased['phase'], df_phased['mag'], yerr=df_phased['err'],
                 fmt='.', color='blue', alpha=0.7, markersize=4)
    ax3.invert_yaxis()
    ax3.set_xlabel('Phase')
    ax3.set_ylabel('Magnitude [mag]')
    ax3.set_title(f'Phased Light Curve (Folded at P = {primary_period:.5f} d)')
    ax3.axvline(x=1.0, color='black', linestyle=':', alpha=0.5)

    # Save the image
    os.makedirs(RESULTS_DIR, exist_ok=True)

    output_filename = os.path.join(RESULTS_DIR, f"lightcurves/{star_id}_analysis.png")

    plt.savefig(output_filename, bbox_inches='tight', dpi=300)
    print(f"\nPlot saved to {output_filename}")
    plt.show()


def analyze_single_star(star_id_num):
    star_id_str = f"OGLE-LMC-CEP-{star_id_num:04d}"
    print(f"--- Starting analysis for {star_id_str} ---")

    filepath = download_ogle_data(star_id_num, download_dir=DATA_DIR)
    if not filepath:
        return

    df_clean = ingest_and_clean(filepath)

    primary_period, freq, power, top_periods, top_powers = find_period(df_clean, min_period=0.1)

    print("\n--- Top Signal Peaks ---")
    print(f"{'Rank':<6} {'Period [d]':<15} {'Power':<8}")
    print("-" * 35)
    for i in range(len(top_periods)):
        print(f"{i + 1:<6} {top_periods[i]:<15.5f} {top_powers[i]:<8.4f}")

    df_phased = fold_light_curve(df_clean, primary_period)

    generate_multipanel_plot(df_clean, df_phased, primary_period, freq, power, top_periods, top_powers, star_id_str)


if __name__ == "__main__":
    #default cepheid
    if len(sys.argv) > 1:
        star_num = int(sys.argv[1])
    else:
        star_num = 1

    analyze_single_star(star_num)
