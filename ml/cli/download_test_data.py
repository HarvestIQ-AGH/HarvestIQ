import requests
from pathlib import Path
from infrastructure.logger import logger
from utilities.path_resolver import DATA_TEST_PATH, resolve_path

def download_test_data():
    download_data('ames.csv', "https://www.openintro.org/book/statdata/ames.csv")

@resolve_path(lambda: DATA_TEST_PATH)
def download_data(filename, url):
    if Path(filename).exists():
        logger.info(f"{filename} already exists, skipping download.")
        return

    logger.info(f"Downloading {url}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/csv,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    with open(filename, "wb") as f:
        f.write(response.content)

    logger.info(f'Success, saved to {filename}')
