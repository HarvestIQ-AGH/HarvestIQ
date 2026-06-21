from pathlib import Path

import joblib
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR

from infrastructure import logger
from infrastructure.local import LocalConfiguration
from models.YieldPredictionXGBoost import YieldPredictionXGBoost
from models.train_me import train_me
from models.yield_preprocessing import make_column_transformer
from utilities import resolve_path

_PARAM_DIST = [
    {
        "regressor__kernel":  ["rbf"],
        "regressor__C":       [0.1, 1.0, 10.0, 100.0, 300.0],
        "regressor__epsilon": [0.01, 0.05, 0.1, 0.2, 0.5],
        "regressor__gamma":   ["scale", "auto", 0.001, 0.01, 0.1],
    },
    {
        "regressor__kernel":  ["linear"],
        "regressor__C":       [0.1, 1.0, 10.0, 100.0, 300.0],
        "regressor__epsilon": [0.01, 0.05, 0.1, 0.2, 0.5],
    },
]


@train_me
class YieldPredictionSVR(YieldPredictionXGBoost):
    def __init__(self, data_engine, config: LocalConfiguration) -> None:
        super().__init__(data_engine, config)

    def feature_engineeeing(self):
        column_transformer = make_column_transformer(
            self._X_train, scale=True, ordinal_categorical=False
        )
        self._pipeline = Pipeline([
            ("transformer", column_transformer),
            ("regressor", SVR()),
        ])
        self.model_lineage.add_metadata_entries(
            numerical_features=self._X_train.select_dtypes(include="number").columns.tolist(),
            categorical_features=["growth_stage"],
            numerical_scaling="standard",
            categorical_encoding="one_hot",
        )
        self.model_lineage.export()

    def train(self):
        search = RandomizedSearchCV(
            self._pipeline,
            param_distributions=_PARAM_DIST,
            n_iter=40,
            cv=10,
            scoring={"rmse": "neg_root_mean_squared_error", "r2": "r2"},
            refit="rmse",
            random_state=42,
            n_jobs=-1,
        )
        search.fit(self._X_train, self._y_train)
        self._pipeline = search.best_estimator_

        best_idx = search.best_index_
        cv_rmse = -search.cv_results_["mean_test_rmse"][best_idx]
        cv_r2 = search.cv_results_["mean_test_r2"][best_idx]

        logger.info(f"Best params: {search.best_params_}")
        logger.info(f"CV R²:   {cv_r2:.4f}")
        logger.info(f"CV RMSE: {cv_rmse:.4f}")

        @resolve_path(self.model_lineage.path)
        def _save():
            joblib.dump(self._pipeline, "yield_svr.joblib")

        _save()

    def load_pretrained(self, path: Path):
        self._pipeline = joblib.load(path / "yield_svr.joblib")
