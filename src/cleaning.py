import pandas as pd
from astropy.stats import sigma_clip

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
    df_clean = df[~filtered_mag.mask].copy()

    # Optional: throw away points with big measurement errors
    # df_clean = df_clean[df_clean['err'] < 0.1]

    # Inverse Variance Weighting
    # In phase B astropy's LombScargle handles errors natively, we pre-calculate
    # weights here for future curve fitting or export.
    df_clean['weight'] = 1.0 / (df_clean['err'] ** 2)

    rejected = original_point_count - len(df_clean)
    print(f"Rejected {rejected} outlier points out of {original_point_count}.")

    return df_clean