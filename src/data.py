import os
import urllib.request

def download_ogle_data(star_id, band="I", download_dir="data"):
    """
    Downloads raw photometric data of a Cepheid from the OGLE-IV database.
    star_id: int, e.g., 1 for OGLE-LMC-CEP-0001
    band: str, photometric filter (e.g., "I", "V", "J", "K")
    """
    os.makedirs(download_dir, exist_ok=True)
    filename_remote = f"OGLE-LMC-CEP-{star_id:04d}.dat"
    filename_local = f"OGLE-LMC-CEP-{star_id:04d}_{band}.dat"
    url = f"https://www.astrouw.edu.pl/ogle/ogle4/OCVS/lmc/cep/phot/{band}/{filename_remote}"
    filepath = os.path.join(download_dir, filename_local)

    if not os.path.exists(filepath):
        print(f"Downloading {band}-band data for CEP-{star_id:04d} from OGLE database...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Download successful: {filename_local}")
        except Exception as e:
            print(f"Download error for {band}-band: {e}")
            return None
    return filepath
