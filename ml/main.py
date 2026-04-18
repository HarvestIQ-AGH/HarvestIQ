import argparse
import shutil

import requests
from cli import clean
from cli.download_test_data import download_test_data
import sklearn

from infrastructure.DataEngine import DataEngine
from infrastructure.logger import logger
from models.test.RegressionModel import RegressionModel
from utilities.path_resolver import DATA_TEST_PATH, ARTIFACTS_DEFAULT_PATH, make_directories

sklearn.set_config(transform_output="pandas")
make_directories()



def run(model_name: str):
    assert model_name == "RegressionModel", f"Unknown model: {model_name}"

    data_engine = DataEngine(path=str('ames.csv'))
    model = RegressionModel(data_engine)

    logger.info("Cleaning data...")
    model.clean_data()

    logger.info("Engineering features...")
    model.feature_engineeeing()

    logger.info("Training...")
    model.train()

    logger.info("Evaluating...")
    model.evaluate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="clean artifacts")
    parser.add_argument("--run", metavar="MODEL", help="Model to run")
    parser.add_argument("--download-data", action="store_true", help="download test datasets")
    args = parser.parse_args()

    if args.clean:
        clean()
    if args.download_data:
        download_test_data()
    if args.run:
        run(args.run)
