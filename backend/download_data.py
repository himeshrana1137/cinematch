import os
import zipfile
import io
import ssl
import urllib.request
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
REQUIRED_FILES = ["movies.csv", "ratings.csv", "links.csv"]

def ensure_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)
    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(DATA_DIR, f))]
    if not missing:
        return True

    print(f"Missing dataset files: {missing}. Downloading MovieLens small dataset...")
    
    zip_content = None
    # 1. Try requests
    try:
        resp = requests.get(DATASET_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            zip_content = resp.content
    except Exception as e:
        print(f"Requests download failed: {e}. Trying urllib with relaxed SSL...")

    # 2. Fallback to urllib with unverified context
    if not zip_content:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(DATASET_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                zip_content = r.read()
        except Exception as e:
            print(f"Urllib download also failed: {e}")
            return False

    try:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
            for member in z.namelist():
                filename = os.path.basename(member)
                if filename in REQUIRED_FILES:
                    target_path = os.path.join(DATA_DIR, filename)
                    with z.open(member) as source, open(target_path, "wb") as target:
                        target.write(source.read())
                    print(f"Extracted {filename} to {target_path}")

        print("MovieLens dataset downloaded and extracted successfully.")
        return True
    except Exception as e:
        print(f"Error extracting MovieLens dataset: {e}")
        return False

if __name__ == "__main__":
    ensure_dataset()
