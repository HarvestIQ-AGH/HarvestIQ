import argparse
import shutil

import requests
import sklearn

from infrastructure.DataEngine import DataEngine
from models.test.RegressionModel import RegressionModel
from utilities.path_resolver import DATA_TEST_PATH, OUTPUT_DEFAULT_PATH, make_directories

sklearn.set_config(transform_output="pandas")
make_directories()

AMES_URL = "https://www.openintro.org/book/statdata/ames.csv"
AMES_PATH = DATA_TEST_PATH / "ames.csv"


def download_data():
    if AMES_PATH.exists():
        print(f"{AMES_PATH} already exists, skipping download.")
        return
    print(f"Downloading {AMES_URL}...")
    response = requests.get(AMES_URL, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
    response.raise_for_status()
    AMES_PATH.write_bytes(response.content)
    print(f"Saved to {AMES_PATH}.")


def clean():
    for path in (DATA_TEST_PATH, OUTPUT_DEFAULT_PATH):
        if path.exists():
            shutil.rmtree(path)
            print(f"Cleaned {path}.")


def run(model_name: str):
    assert model_name == "RegressionModel", f"Unknown model: {model_name}"

    data_engine = DataEngine(path=str(AMES_PATH))
    model = RegressionModel(data_engine)

    print("Cleaning data...")
    model.clean_data()

    print("Engineering features...")
    model.feature_engineeeing()

    print("Training...")
    model.train()

    print("Evaluating...")
    model.evaluate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Remove test data directory")
    parser.add_argument("--run", metavar="MODEL", help="Model to run")
    parser.add_argument("--download-data", action="store_true", help="Download Ames dataset")
    args = parser.parse_args()

    if args.clean:
        clean()
    if args.download_data:
        download_data()
    if args.run:
        run(args.run)
