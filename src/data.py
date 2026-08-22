import os
import urllib.request

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

    return filepath
