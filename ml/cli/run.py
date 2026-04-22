from infrastructure import DataEngine, ModelExecutor, Stage, load_model_class
from infrastructure.local import LocalConfiguration


def run(model_name: str, config: LocalConfiguration, stop_stage: int = Stage.TRAINING):
    model_cls = load_model_class(model_name, config.paths.models.resolve())
    model = model_cls(DataEngine(), config)
    ModelExecutor(model).run(stop_stage)
