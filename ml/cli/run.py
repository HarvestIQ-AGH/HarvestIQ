from infrastructure.data_engine import DataEngine
from infrastructure.local.local_config import LocalConfiguration
from infrastructure.model_executor import ModelExecutor, Stage
from infrastructure.model_loader import load_model_class


def run(model_name: str, config: LocalConfiguration, stop_stage: int = Stage.TRAINING):
    model_cls = load_model_class(model_name, config.paths.models.resolve())
    model = model_cls(DataEngine(), config)
    ModelExecutor(model).run(stop_stage)
