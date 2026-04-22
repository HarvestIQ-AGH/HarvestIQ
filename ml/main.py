import argparse
import warnings

import sklearn

warnings.filterwarnings("ignore", category=UserWarning, module=r"feature_engine\..*")

from cli import clean, download_test_data, from_pretrained, run, visualize
from infrastructure.local import LocalConfiguration, Mode
from utilities import make_directories

sklearn.set_config(transform_output="pandas")
make_directories()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="clean artifacts")
    parser.add_argument("--run", metavar="MODEL", help="model name (required with --train, --from-pretrained, or --visualize)")
    parser.add_argument("--test", action="store_true", help="use data/test and models/test directories")
    parser.add_argument("--download-data", action="store_true", help="download test datasets")
    parser.add_argument("--train", action="store_true", help="train the model specified by --run")
    parser.add_argument("--from-pretrained", action="store_true", help="load latest saved weights for --run model and evaluate")
    parser.add_argument("--stop-stage", type=int, metavar="N", default=5, help="run pipeline up to stage N (1-5, default=5). Used with --train.")
    parser.add_argument("--visualize", action="store_true", help="display saved analysis plots for --run model")
    args = parser.parse_args()

    if args.train and args.from_pretrained:
        parser.error("--train and --from-pretrained are mutually exclusive")
    if not (1 <= args.stop_stage <= 5):
        parser.error("--stop-stage must be between 1 and 5")

    config = LocalConfiguration(Mode.TEST if args.test else Mode.DEFAULT)

    if args.clean:
        clean()
    if args.download_data:
        download_test_data()
    if args.train:
        if not args.run:
            parser.error("--train requires --run MODEL")
        run(args.run, config, stop_stage=args.stop_stage)
    elif args.from_pretrained:
        if not args.run:
            parser.error("--from-pretrained requires --run MODEL")
        from_pretrained(args.run, config)
    elif args.visualize:
        if not args.run:
            parser.error("--visualize requires --run MODEL")
        visualize(args.run, config)
    elif args.run:
        parser.error("--run requires --train, --from-pretrained, or --visualize")
