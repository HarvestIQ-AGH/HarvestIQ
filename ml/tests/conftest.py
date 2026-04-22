import dataclasses
import io
import os
import types

import pytest
import sklearn

from infrastructure.local.local_config import TEST_PATHS
from infrastructure.local.mode import Mode
from models.model_lineage import ModelLineage


@pytest.fixture(autouse=True, scope="session")
def sklearn_pandas_output():
    sklearn.set_config(transform_output="pandas")


@pytest.fixture(autouse=True)
def restore_cwd():
    cwd = os.getcwd()
    yield
    os.chdir(cwd)


@pytest.fixture(autouse=True)
def reset_model_lineage():
    yield
    ModelLineage.MODEL_NAME = None


@pytest.fixture
def isolated_config(tmp_path):
    isolated_paths = dataclasses.replace(TEST_PATHS, artifacts=tmp_path / "artifacts")
    return types.SimpleNamespace(mode=Mode.TEST, device="cpu", paths=isolated_paths)


@pytest.fixture
def real_test_config():
    from infrastructure.local.local_config import LocalConfiguration
    return LocalConfiguration(Mode.TEST)


@pytest.fixture
def regression_model_trained(isolated_config):
    if not (isolated_config.paths.data / "ames.csv").exists():
        pytest.skip("data/test/ames.csv not found — run --download-data first")
    from infrastructure.data_engine import DataEngine
    from infrastructure.model_executor import ModelExecutor, Stage
    from models.test.RegressionModel import RegressionModel
    model = RegressionModel(DataEngine(), isolated_config)
    ModelExecutor(model).run(Stage.TRAINING)
    return model


@pytest.fixture
def fake_png_bytes():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()
