import argparse
import warnings

import sklearn

warnings.filterwarnings("ignore", category=UserWarning, module=r"feature_engine\..*")

from cli import clean
from cli.download_test_data import download_test_data
from cli.from_pretrained import from_pretrained
from cli.run import run
from infrastructure.local.local_config import LocalConfiguration
from infrastructure.local.mode import Mode
from utilities.path_resolver import make_directories

sklearn.set_config(transform_output="pandas")
make_directories()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="clean artifacts")
    parser.add_argument("--run", metavar="MODEL", help="model name (required with --train or --from-pretrained)")
    parser.add_argument("--test", action="store_true", help="use data/test and models/test directories")
    parser.add_argument("--download-data", action="store_true", help="download test datasets")
    parser.add_argument("--train", action="store_true", help="train the model specified by --run")
    parser.add_argument("--from-pretrained", action="store_true", help="load latest saved weights for --run model and evaluate")
    args = parser.parse_args()

    if args.train and args.from_pretrained:
        parser.error("--train and --from-pretrained are mutually exclusive")

    config = LocalConfiguration(Mode.TEST if args.test else Mode.DEFAULT)

    if args.clean:
        clean()
    if args.download_data:
        download_test_data()
    if args.train:
        if not args.run:
            parser.error("--train requires --run MODEL")
        run(args.run, config)
    elif args.from_pretrained:
        if not args.run:
            parser.error("--from-pretrained requires --run MODEL")
        from_pretrained(args.run, config)
    elif args.run:
        parser.error("--run requires --train or --from-pretrained")
