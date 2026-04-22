import json
import os
from pathlib import Path

from models.model_base import ModelBase
from utilities.path_resolver import resolve_path


class ModelLineage:
    MODEL_NAME: str | None = None

    def __init__(self, model_class: ModelBase, artifacts_path: Path) -> None:
        self.model_metadata = {}
        self.path: Path | None = None
        self._artifacts_path = artifacts_path
        ModelLineage.MODEL_NAME = type(model_class).__name__

    def add_metadata_entries(self, **kwargs):
        for key, value in kwargs.items():
            self.model_metadata[key] = value

    def export(self):
        self.path = self._lineage_path().resolve()

        @resolve_path(self.path)
        def _write():
            with open(f"{self.path.name}_metadata.json", "w") as f:
                json.dump(
                    self.model_metadata, f, default=_serialize_estimator, indent=2
                )

        _write()

    def _model_dir(self) -> Path:
        assert ModelLineage.MODEL_NAME is not None
        return self._artifacts_path / ModelLineage.MODEL_NAME

    def _version(self) -> int:
        model_dir = self._model_dir()
        assert model_dir.exists()
        latest = max(
            [0]
            + [
                int(x.name.split("_v")[1])
                for x in os.scandir(model_dir)
                if x.is_dir() and x.name.startswith(f"{ModelLineage.MODEL_NAME}_v")
            ]
        )
        return latest + 1

    def _lineage_name(self) -> str:
        return f"{ModelLineage.MODEL_NAME}_v{self._version()}"

    def _lineage_path(self) -> Path:
        model_dir = self._model_dir()
        os.makedirs(model_dir, exist_ok=True)
        return model_dir / self._lineage_name()


def _serialize_estimator(obj):
    if hasattr(obj, "get_params"):
        return {"class": type(obj).__name__, "params": obj.get_params(deep=False)}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
