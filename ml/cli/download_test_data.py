import tarfile
from pathlib import Path

import requests

from infrastructure.local.local_config import TEST_PATHS
from infrastructure.logger import logger
from utilities.path_resolver import resolve_path

_AMES_URL = "https://www.openintro.org/book/statdata/ames.csv"
_AMES_FILE = "ames.csv"
_ABO_URL = (
    "https://amazon-berkeley-objects.s3.amazonaws.com/archives/abo-images-small.tar"
)
_ABO_TAR = "abo-images-small.tar"


def download_test_data():
    _download_ames()
    _download_abo()


def _download_ames():
    _download_file(_AMES_FILE, _AMES_URL)


def _download_abo():
    if (TEST_PATHS.data / "images").exists():
        logger.info("ABO images already exist, skipping download.")
        return
    _download_file(_ABO_TAR, _ABO_URL, stream=True)
    _extract_abo_tar()


@resolve_path(lambda: TEST_PATHS.data)
def _download_file(filename: str, url: str, stream: bool = False):
    if Path(filename).exists():
        logger.info(f"{filename} already exists, skipping.")
        return
    logger.info(f"Downloading {url}...")
    with requests.get(
        url, headers={"User-Agent": "Mozilla/5.0"}, stream=stream, timeout=60
    ) as response:
        response.raise_for_status()
        with open(filename, "wb") as f:
            if stream:
                for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                    f.write(chunk)
            else:
                f.write(response.content)
    logger.info(f"Saved to {filename}.")


@resolve_path(lambda: TEST_PATHS.data)
def _extract_abo_tar():
    logger.info(f"Extracting {_ABO_TAR}...")
    with tarfile.open(_ABO_TAR) as tar:
        tar.extractall(".")
    Path(_ABO_TAR).unlink()
    logger.info("Extraction complete, tar removed.")
