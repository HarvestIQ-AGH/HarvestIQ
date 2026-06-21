from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline

from infrastructure import logger
from infrastructure.local import LocalConfiguration
from models.YieldPredictionXGBoost import YieldPredictionXGBoost
from models.train_me import train_me
from models.yield_preprocessing import make_column_transformer
from utilities import resolve_path

_PARAM_DIST = {
    "regressor__n_estimators":      [300, 500, 700, 1000],
    "regressor__max_depth":         [None, 8, 12, 16, 20],
    "regressor__min_samples_split": [2, 5, 10],
    "regressor__min_samples_leaf":  [1, 2, 4],
    "regressor__max_features":      ["sqrt", "log2", 0.5, 0.8, 1.0],
    "regressor__bootstrap":         [True],
}


@train_me
class YieldPredictionRandomForest(YieldPredictionXGBoost):
    def __init__(self, data_engine, config: LocalConfiguration) -> None:
        super().__init__(data_engine, config)

    def feature_engineeeing(self):
        column_transformer = make_column_transformer(
            self._X_train, scale=False, ordinal_categorical=False
        )
        self._pipeline = Pipeline([
            ("transformer", column_transformer),
            ("regressor", RandomForestRegressor(random_state=42, n_jobs=-1)),
        ])
        self.model_lineage.add_metadata_entries(
            numerical_features=self._X_train.select_dtypes(include="number").columns.tolist(),
            categorical_features=["growth_stage"],
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

        self._save_feature_importance()

        @resolve_path(self.model_lineage.path)
        def _save():
            joblib.dump(self._pipeline, "yield_random_forest.joblib")

        _save()

    def load_pretrained(self, path: Path):
        self._pipeline = joblib.load(path / "yield_random_forest.joblib")

    def _save_feature_importance(self) -> None:
        analysis_features_path = self._analysis_path / "features"
        forest = self._pipeline.named_steps["regressor"]
        importance = pd.Series(
            forest.feature_importances_,
            index=self._pipeline.named_steps["transformer"].get_feature_names_out(),
        ).sort_values()

        @resolve_path(lambda: analysis_features_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 10))
            importance.plot(kind="barh", ax=ax)
            ax.set_title("Random Forest feature importances (tuned model)")
            ax.set_xlabel("Importance")
            ax.axvline(0, color="black", linewidth=0.8)
            fig.tight_layout()
            fig.savefig("feature_importances.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("Feature importance plot saved.")
