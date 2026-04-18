from pathlib import Path

from infrastructure.DataEngine import DataEngine
from infrastructure.logger import logger
from infrastructure.model_loader import load_model_class
from utilities.path_resolver import DATA_DEFAULT_PATH, DATA_TEST_PATH

_MODELS_ROOT = Path("models")
_MODELS_TEST_ROOT = _MODELS_ROOT / "test"


def run(model_name: str, dataset: str, test: bool = False):
    data_root = DATA_TEST_PATH if test else DATA_DEFAULT_PATH
    models_root = (_MODELS_TEST_ROOT if test else _MODELS_ROOT).resolve()
    dataset_path = (data_root / dataset).resolve()

    model_cls = load_model_class(model_name, models_root)
    model = model_cls(DataEngine(path=str(dataset_path)))

    logger.info("Cleaning data...")
    model.clean_data()

    logger.info("Engineering features...")
    model.feature_engineeeing()

    logger.info("Training...")
    model.train()

    logger.info("Evaluating...")
    model.evaluate()
