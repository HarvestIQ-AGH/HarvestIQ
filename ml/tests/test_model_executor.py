import pytest

from infrastructure import DataEngine, ModelExecutor, Stage
from models import ModelBase


class RecordingStubModel(ModelBase):
    def __init__(self, data_engine, config):
        super().__init__(data_engine, config)
        self.call_log = []

    def clean_data(self):
        self.call_log.append("clean_data")

    def analyze_data(self):
        self.call_log.append("analyze_data")

    def feature_engineeeing(self):
        self.call_log.append("feature_engineeeing")

    def analyze_features(self):
        self.call_log.append("analyze_features")

    def train(self):
        self.call_log.append("train")

    def evaluate(self):
        self.call_log.append("evaluate")

    def load_pretrained(self, path):
        self.call_log.append("load_pretrained")


@pytest.fixture
def stub_model(isolated_config):
    return RecordingStubModel(DataEngine(), isolated_config)


def test_stop_stage_1(stub_model):
    ModelExecutor(stub_model).run(1)
    assert stub_model.call_log == ["clean_data"]


def test_stop_stage_2(stub_model):
    ModelExecutor(stub_model).run(2)
    assert stub_model.call_log == ["clean_data", "analyze_data"]


def test_stop_stage_3(stub_model):
    ModelExecutor(stub_model).run(3)
    assert stub_model.call_log == ["clean_data", "analyze_data", "feature_engineeeing"]


def test_stop_stage_4(stub_model):
    ModelExecutor(stub_model).run(4)
    assert stub_model.call_log == [
        "clean_data", "analyze_data", "feature_engineeeing", "analyze_features"
    ]


def test_stop_stage_5_full(stub_model):
    ModelExecutor(stub_model).run(5)
    assert stub_model.call_log == [
        "clean_data", "analyze_data", "feature_engineeeing",
        "analyze_features", "train", "evaluate",
    ]


def test_default_is_stage_5(stub_model):
    ModelExecutor(stub_model).run()
    assert stub_model.call_log == [
        "clean_data", "analyze_data", "feature_engineeeing",
        "analyze_features", "train", "evaluate",
    ]


def test_invalid_stage_raises(stub_model):
    with pytest.raises(ValueError):
        ModelExecutor(stub_model).run(0)


def test_train_and_evaluate_both_called(stub_model):
    ModelExecutor(stub_model).run(Stage.TRAINING)
    assert stub_model.call_log.count("train") == 1
    assert stub_model.call_log.count("evaluate") == 1
