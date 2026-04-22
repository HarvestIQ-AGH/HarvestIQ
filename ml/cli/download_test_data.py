import tarfile

import requests
from pathlib import Path
from infrastructure.logger import logger
from utilities.path_resolver import DATA_TEST_PATH, resolve_path

_ABO_URL = "https://amazon-berkeley-objects.s3.amazonaws.com/archives/abo-images-small.tar"
_ABO_TAR = "abo-images-small.tar"
_ABO_IMAGES_DIR = "images"


def download_test_data():
    download_data('ames.csv', "https://www.openintro.org/book/statdata/ames.csv")
    download_abo_data()


def download_abo_data():
    images_dir = DATA_TEST_PATH / _ABO_IMAGES_DIR
    if images_dir.exists():
        logger.info(f"{images_dir} already exists, skipping ABO download.")
        return
    _download_abo_tar()
    _extract_abo_tar()


@resolve_path(lambda: DATA_TEST_PATH)
def _download_abo_tar():
    if Path(_ABO_TAR).exists():
        return
    logger.info(f"Downloading ABO dataset from {_ABO_URL} (~3 GB)...")
    headers = {"User-Agent": "Mozilla/5.0"}
    with requests.get(_ABO_URL, headers=headers, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(_ABO_TAR, "wb") as f:
            for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                f.write(chunk)
    logger.info(f"Saved to {_ABO_TAR}.")


@resolve_path(lambda: DATA_TEST_PATH)
def _extract_abo_tar():
    logger.info(f"Extracting {_ABO_TAR}...")
    with tarfile.open(_ABO_TAR) as tar:
        tar.extractall(".")
    Path(_ABO_TAR).unlink()
    logger.info("Extraction complete, tar removed.")

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
