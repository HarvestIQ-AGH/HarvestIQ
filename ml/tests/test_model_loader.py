import pytest

from infrastructure.model_loader import load_model_class


_STUB = """\
from models.train_me import train_me
from models.model_base import ModelBase

@train_me
class {name}(ModelBase):
    def clean_data(self): pass
    def feature_engineeeing(self): pass
    def train(self): pass
    def evaluate(self): pass
    def load_pretrained(self, path): pass
"""

_NO_DECORATOR = """\
from models.model_base import ModelBase

class PlainModel(ModelBase):
    def clean_data(self): pass
    def feature_engineeeing(self): pass
    def train(self): pass
    def evaluate(self): pass
    def load_pretrained(self, path): pass
"""

_TWO_DECORATED = """\
from models.train_me import train_me
from models.model_base import ModelBase

@train_me
class ModelA(ModelBase):
    def clean_data(self): pass
    def feature_engineeeing(self): pass
    def train(self): pass
    def evaluate(self): pass
    def load_pretrained(self, path): pass

@train_me
class ModelB(ModelBase):
    def clean_data(self): pass
    def feature_engineeeing(self): pass
    def train(self): pass
    def evaluate(self): pass
    def load_pretrained(self, path): pass
"""


def test_finds_train_me_class(tmp_path):
    (tmp_path / "FooModel.py").write_text(_STUB.format(name="FooModel"))
    cls = load_model_class("FooModel", tmp_path)
    assert cls.__name__ == "FooModel"


def test_returned_class_is_instantiable(tmp_path, isolated_config):
    (tmp_path / "FooModel.py").write_text(_STUB.format(name="FooModel"))
    from infrastructure.data_engine import DataEngine
    cls = load_model_class("FooModel", tmp_path)
    instance = cls(DataEngine(), isolated_config)
    assert instance is not None


def test_no_train_me_raises_value_error(tmp_path):
    (tmp_path / "PlainModel.py").write_text(_NO_DECORATOR)
    with pytest.raises(ValueError, match="No @train_me"):
        load_model_class("PlainModel", tmp_path)


def test_multiple_train_me_raises_value_error(tmp_path):
    (tmp_path / "TwoModel.py").write_text(_TWO_DECORATED)
    with pytest.raises(ValueError, match="Multiple @train_me"):
        load_model_class("TwoModel", tmp_path)


def test_file_not_found_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_model_class("Ghost", tmp_path)


def test_ambiguous_name_raises(tmp_path):
    sub1 = tmp_path / "a"
    sub2 = tmp_path / "b"
    sub1.mkdir()
    sub2.mkdir()
    (sub1 / "AmbigModel.py").write_text(_STUB.format(name="AmbigModel"))
    (sub2 / "AmbigModel.py").write_text(_STUB.format(name="AmbigModel"))
    with pytest.raises(ValueError, match="Ambiguous"):
        load_model_class("AmbigModel", tmp_path)


def test_finds_in_subdirectory(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "SubModel.py").write_text(_STUB.format(name="SubModel"))
    cls = load_model_class("SubModel", tmp_path)
    assert cls.__name__ == "SubModel"
