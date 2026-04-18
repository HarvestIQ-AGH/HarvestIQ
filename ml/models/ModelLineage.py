import json
import os
from pathlib import Path

from models.ModelBase import ModelBase
from utilities.path_resolver import ARTIFACTS_TEST_PATH, resolve_path


class ModelLineage:
    MODEL_NAME: str | None = None

    def __init__(self, model_class: ModelBase) -> None:
        self.model_metadata = {}
        self.path: Path | None = None
        ModelLineage.MODEL_NAME = type(model_class).__name__

    def add_metadata_entries(self, **kwargs):
        for key, value in kwargs.items():
            self.model_metadata[key] = value

    def export(self):
        self.path = get_model_lineage_path().resolve()

        @resolve_path(self.path)
        def _write():
            with open(f"{self.path.name}_metadata.json", "w") as f:
                json.dump(self.model_metadata, f, default=_serialize_estimator, indent=2)

        _write()


def _serialize_estimator(obj):
    if hasattr(obj, "get_params"):
        return {"class": type(obj).__name__, "params": obj.get_params(deep=False)}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def get_model_version():
    assert ModelLineage.MODEL_NAME is not None

    model_dir = ARTIFACTS_TEST_PATH / ModelLineage.MODEL_NAME
    assert model_dir.exists() is True

    latest = max(
        [0]
        + [
            int(x.name.split("_v")[1])
            for x in os.scandir(model_dir)
            if x.is_dir() and x.name.startswith(f"{ModelLineage.MODEL_NAME}_v")
        ]
    )
    return latest + 1


def get_model_lineage_name():
    assert ModelLineage.MODEL_NAME is not None

    return f"{ModelLineage.MODEL_NAME}_v{get_model_version()}"


def get_model_lineage_path():
    model_dir = ARTIFACTS_TEST_PATH / ModelLineage.MODEL_NAME
    os.makedirs(model_dir, exist_ok=True)
    return model_dir / Path(get_model_lineage_name())
