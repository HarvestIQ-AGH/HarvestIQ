import json

from models.model_lineage import ModelLineage


class FakeModel:
    pass


def test_model_name_set_from_instance_type(isolated_config):
    ModelLineage(FakeModel(), isolated_config.paths.artifacts)
    assert ModelLineage.MODEL_NAME == "FakeModel"


def test_first_export_creates_v1_dir(isolated_config):
    lineage = ModelLineage(FakeModel(), isolated_config.paths.artifacts)
    lineage.export()
    expected = isolated_config.paths.artifacts / "FakeModel" / "FakeModel_v1"
    assert expected.exists()


def test_second_export_creates_v2_dir(isolated_config):
    lineage1 = ModelLineage(FakeModel(), isolated_config.paths.artifacts)
    lineage1.export()
    lineage2 = ModelLineage(FakeModel(), isolated_config.paths.artifacts)
    lineage2.export()
    assert (isolated_config.paths.artifacts / "FakeModel" / "FakeModel_v2").exists()


def test_metadata_json_written(isolated_config):
    lineage = ModelLineage(FakeModel(), isolated_config.paths.artifacts)
    lineage.export()
    metadata_file = lineage.path / f"{lineage.path.name}_metadata.json"
    assert metadata_file.exists()
    json.loads(metadata_file.read_text())


def test_metadata_contains_added_entries(isolated_config):
    lineage = ModelLineage(FakeModel(), isolated_config.paths.artifacts)
    lineage.add_metadata_entries(foo=42, bar="hello")
    lineage.export()
    metadata_file = lineage.path / f"{lineage.path.name}_metadata.json"
    data = json.loads(metadata_file.read_text())
    assert data["foo"] == 42
    assert data["bar"] == "hello"


def test_path_set_after_export(isolated_config):
    lineage = ModelLineage(FakeModel(), isolated_config.paths.artifacts)
    assert lineage.path is None
    lineage.export()
    assert lineage.path is not None
    assert lineage.path.is_dir()
