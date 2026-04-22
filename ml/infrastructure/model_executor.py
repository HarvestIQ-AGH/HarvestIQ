from enum import IntEnum

from .logger import logger
from models import ModelBase


class Stage(IntEnum):
    DATA_LOADING        = 1
    DATA_ANALYSIS       = 2
    FEATURE_ENGINEERING = 3
    FEATURE_ANALYSIS    = 4
    TRAINING            = 5


class ModelExecutor:
    def __init__(self, model: ModelBase) -> None:
        self._model = model

    def run(self, stop_stage: int = Stage.TRAINING) -> None:
        stop_stage = Stage(stop_stage)
        stages = [
            (Stage.DATA_LOADING,        "Data loading",          self._model.clean_data),
            (Stage.DATA_ANALYSIS,       "Data analysis",         self._model.analyze_data),
            (Stage.FEATURE_ENGINEERING, "Feature engineering",   self._model.feature_engineeeing),
            (Stage.FEATURE_ANALYSIS,    "Feature analysis",      self._model.analyze_features),
            (Stage.TRAINING,            "Training + evaluation", self._train_and_evaluate),
        ]
        for stage, label, action in stages:
            if stage > stop_stage:
                logger.info(f"Stopped at stage {stop_stage.value} ({stop_stage.name}).")
                break
            logger.info(f"[Stage {stage.value}/{len(Stage)}] {label}...")
            action()
            logger.info(f"[Stage {stage.value}/{len(Stage)}] {label} complete.")

    def _train_and_evaluate(self) -> None:
        self._model.train()
        self._model.evaluate()
