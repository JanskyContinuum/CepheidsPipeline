import os
import urllib.request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import sigma_clip
from astropy.timeseries import LombScargle


def download_ogle_data(star_id, download_dir="data"):
    """
    Downloads raw photometric data of a Cepheid from the OGLE-IV database.
    star_id: int, e.g., 1 for OGLE-LMC-CEP-0001
    """
    os.makedirs(download_dir, exist_ok=True)
    filename = f"OGLE-LMC-CEP-{star_id:04d}.dat"
    url = f"https://www.astrouw.edu.pl/ogle/ogle4/OCVS/lmc/cep/phot/I/{filename}"
    filepath = os.path.join(download_dir, filename)

    if not os.path.exists(filepath):
        print(f"Downloading file {filename} from OGLE database...")
        try:
            # Spoofing user agent so the server doesn't reject the request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            print("Download successful.")
        except Exception as e:
            print(f"Download error: {e}")
            return None

    return filepath, filename


def ingest_and_clean(filepath):
    """
    Ingests a .dat file, removes outliers and calculates statistical weights.
    """

    # Columns: HJD (Time), mag (Magnitude), err (Measurement error)
    df = pd.read_csv(filepath, sep=r'\s+', names=['HJD', 'mag', 'err'])

    original_point_count = len(df)

    # Sigma-Clipping
    # Returns a MaskedArray, where rejected points have a True mask.
    filtered_mag = sigma_clip(df['mag'], sigma=3.0, maxiters=3)

    # Create a new, clean dataframe keeping only "unmasked" (good) measurements.
    # The tilde (~) inverts the mask from True to False.
    df_clean = df[~filtered_mag.mask].copy()

    # Optional: throw away points with big measurement errors
    # df_clean = df_clean[df_clean['err'] < 0.1]

    # Inverse Variance Weighting
    # In phase B astropy's LombScargle handles errors natively, we pre-calculate
    # weights here for future curve fitting or export.
    df_clean['weight'] = 1.0 / (df_clean['err'] ** 2)

    rejected = original_point_count - len(df_clean)
    print(f"Phase A completed. Rejected {rejected} outlier points out of {original_point_count}.")

    return df_clean


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

    # Initialize the Lomb-Scargle model
    ls = LombScargle(time, mag, err)

    # Define the frequency grid to search
    min_freq = 1.0 / max_period
    max_freq = 1.0 / min_period

    frequency, power = ls.autopower(minimum_frequency=min_freq, maximum_frequency=max_freq)

    # Identify the highest peak
    best_index = np.argmax(power)
    best_freq = frequency[best_index]
    best_period = 1.0 / best_freq
    max_power = power[best_index]

    print(f"Best period found: {best_period:.5f} days (Power: {max_power:.2f})")

    return best_period, frequency, power


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



if __name__ == "__main__":
    filepath, filename = download_ogle_data(1)

    if filepath:
        # Phase A
        clean_data = ingest_and_clean(filepath)

        # Phase B (using the lower min_period to avoid daily aliasing)
        best_period, freq, power = find_period(clean_data, min_period=0.1)

        # Phase C
        df_phased = fold_light_curve(clean_data, best_period)

        # Visualization
        fig, axes = plt.subplots(3, 1, figsize=(12, 12), gridspec_kw={'hspace': 0.4})

        # Top Panel: Raw Time Series (Time vs Mag)

        ax1 = axes[0]
        ax1.errorbar(clean_data['HJD'], clean_data['mag'], yerr=clean_data['err'],
                     fmt='.', color='gray', alpha=0.5, markersize=3)
        ax1.invert_yaxis()
        ax1.set_xlabel('Time [HJD]')
        ax1.set_ylabel('Magnitude [mag]')
        ax1.set_title('Top Panel: Cleaned Time Series (Raw Data)')


        # Middle Panel: Periodogram (Period vs Power)

        ax2 = axes[1]
        periods_to_plot = 1.0 / freq
        ax2.plot(periods_to_plot, power, color='purple', linewidth=1)

        # best period found
        ax2.axvline(x=best_period, color='red', linestyle='--',
                    label=f'Primary Signal: P = {best_period:.4f} days')

        ax2.set_xlabel('Period [days]')
        ax2.set_ylabel('Lomb-Scargle Power')
        ax2.set_title('Middle Panel: Frequency Analysis (Lomb-Scargle Periodogram)')
        ax2.set_xlim(0.1, 15)
        ax2.legend(loc='upper right')


        # Bottom Panel: Phased Light Curve (Phase vs Mag)

        ax3 = axes[2]
        ax3.errorbar(df_phased['phase'], df_phased['mag'], yerr=df_phased['err'],
                     fmt='.', color='blue', alpha=0.7, markersize=4)
        ax3.invert_yaxis()
        ax3.set_xlabel('Phase')
        ax3.set_ylabel('Magnitude [mag]')
        ax3.set_title(f'Bottom Panel: Phased Light Curve (Folded at P = {best_period:.5f} d)')

        ax3.axvline(x=1.0, color='black', linestyle=':', alpha=0.5)

        # Save the plot to the data folder
        output_filename = "data/pipeline_output_" + filename + ".png"
        plt.savefig(output_filename, bbox_inches='tight', dpi=300)
        print(f"Plot saved successfully as {output_filename}")

        plt.show()