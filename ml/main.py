import argparse
import warnings

import sklearn

warnings.filterwarnings("ignore", category=UserWarning, module=r"feature_engine\..*")

from cli import clean
from cli.download_test_data import download_test_data
from cli.run import run
from utilities.path_resolver import make_directories

sklearn.set_config(transform_output="pandas")
make_directories()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="clean artifacts")
    parser.add_argument("--run", metavar="MODEL", help="Model to run")
    parser.add_argument("--dataset", metavar="FILE", default="ames.csv", help="dataset filename or path (default: ames.csv)")
    parser.add_argument("--test", action="store_true", help="use data/test and models/test directories")
    parser.add_argument("--download-data", action="store_true", help="download test datasets")
    args = parser.parse_args()

    if args.clean:
        clean()
    if args.download_data:
        download_test_data()
    if args.run:
        run(args.run, args.dataset, args.test)
