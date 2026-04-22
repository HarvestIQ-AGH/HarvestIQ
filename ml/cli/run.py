from infrastructure.data_engine import DataEngine
from infrastructure.local.local_config import LocalConfiguration
from infrastructure.logger import logger
from infrastructure.model_loader import load_model_class


def run(model_name: str, config: LocalConfiguration):
    models_root = config.paths.models.resolve()

    model_cls = load_model_class(model_name, models_root)
    model = model_cls(DataEngine(), config)

    logger.info("Cleaning data...")
    model.clean_data()

    logger.info("Engineering features...")
    model.feature_engineeeing()

    logger.info("Training...")
    model.train()

    logger.info("Evaluating...")
    model.evaluate()
