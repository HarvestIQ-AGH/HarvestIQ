from pathlib import Path

import pytest
from sklearn.compose import ColumnTransformer

from infrastructure.data_engine import DataEngine
from infrastructure.model_executor import ModelExecutor, Stage
from models.test.RegressionModel import RegressionModel

pytestmark = pytest.mark.slow


def _skip_if_no_ames(config):
    if not (config.paths.data / "ames.csv").exists():
        pytest.skip("data/test/ames.csv not found — run --download-data first")


def _make_model(config):
    return RegressionModel(DataEngine(), config)


def test_clean_data_populates_splits(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    model.clean_data()
    assert hasattr(model, "_X_train_raw")
    assert hasattr(model, "_X_test_raw")
    assert len(model._X_train_raw) > 0
    assert len(model._y_train) == len(model._X_train_raw)


def test_feature_engineering_creates_transformer(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.FEATURE_ENGINEERING)
    assert isinstance(model._column_transformer, ColumnTransformer)


def test_analyze_data_creates_raw_plots(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.DATA_ANALYSIS)
    raw_dir = model._analysis_path / "raw"
    assert (raw_dir / "saleprice_distribution.png").exists()
    assert (raw_dir / "correlation_heatmap.png").exists()


def test_analyze_features_creates_features_plot(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.FEATURE_ANALYSIS)
    features_dir = model._analysis_path / "features"
    assert (features_dir / "numerical_feature_distributions.png").exists()


def test_train_saves_all_joblibs(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.TRAINING)
    lineage_path = model.model_lineage.path
    assert (lineage_path / "ames_transformer.joblib").exists()
    assert (lineage_path / "price_estimator.joblib").exists()
    assert (lineage_path / "low_price_estimator.joblib").exists()
    assert (lineage_path / "high_price_estimator.joblib").exists()


def test_evaluate_runs_without_error(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.TRAINING)
    model.evaluate()


def test_executor_full_pipeline(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run()


def test_stop_stage_2_no_feature_plots(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.DATA_ANALYSIS)
    assert not (model._analysis_path / "features").exists()


def test_stop_stage_3_no_training_artifacts(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.FEATURE_ENGINEERING)
    lineage_path = model.model_lineage.path
    assert lineage_path is not None
    assert not (lineage_path / "price_estimator.joblib").exists()


def test_load_pretrained_then_evaluate(isolated_config):
    _skip_if_no_ames(isolated_config)
    model = _make_model(isolated_config)
    ModelExecutor(model).run(Stage.TRAINING)
    saved_path = model.model_lineage.path

    model2 = _make_model(isolated_config)
    model2.clean_data()
    model2.load_pretrained(saved_path)
    model2.evaluate()
