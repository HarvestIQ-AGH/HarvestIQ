from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from infrastructure import logger
from infrastructure.local import LocalConfiguration
from infrastructure.logger import LoggerMixin
from models import ModelBase, ModelLineage
from models.train_me import train_me
from models.yield_preprocessing import load_and_clean, make_column_transformer
from utilities import resolve_path

_PARAM_DIST = {
    "regressor__n_estimators":      [300, 500, 700, 1000],
    "regressor__max_depth":         [3, 4, 5],
    "regressor__learning_rate":     [0.01, 0.03, 0.05, 0.08],
    "regressor__subsample":         [0.6, 0.7, 0.8],
    "regressor__colsample_bytree":  [0.5, 0.6, 0.7, 0.8],
    "regressor__colsample_bylevel": [0.5, 0.6, 0.7, 1.0],
    "regressor__min_child_weight":  [3, 5, 7, 10],
    "regressor__gamma":             [0.1, 0.2, 0.3, 0.5],
    "regressor__reg_alpha":         [0.01, 0.1, 0.5, 1.0],
    "regressor__reg_lambda":        [1.0, 2.0, 5.0, 10.0],
}


@train_me
class YieldPredictionXGBoost(ModelBase, LoggerMixin):
    def __init__(self, data_engine, config: LocalConfiguration) -> None:
        super().__init__(data_engine, config)
        self.model_lineage = ModelLineage(self, config.paths.artifacts)

    def clean_data(self):
        df = load_and_clean(self.data_engine, self.config.paths.data / "yield-interpol-indeces.db")
        y = df.pop("YIELD")
        self._X_train, self._X_test, self._y_train, self._y_test = train_test_split(
            df, y, test_size=0.2, random_state=42
        )
        logger.info(
            f"clean_data: {len(df)} samples after dedup — "
            f"train={len(self._X_train)}, test={len(self._X_test)}"
        )

    def analyze_data(self) -> None:
        pass

    def feature_engineeeing(self):
        column_transformer = make_column_transformer(
            self._X_train, scale=False, ordinal_categorical=True
        )
        self._pipeline = Pipeline([
            ("transformer", column_transformer),
            ("regressor", XGBRegressor(random_state=42, n_jobs=-1)),
        ])
        self.model_lineage.add_metadata_entries(
            numerical_features=self._X_train.select_dtypes(include="number").columns.tolist(),
            categorical_features=["growth_stage"],
        )
        self.model_lineage.export()

    def analyze_features(self) -> None:
        analysis_features_path = self._analysis_path / "features"

        # Fit only the transformer — no need to run XGBoost here
        transformer = self._pipeline.named_steps["transformer"]
        feat_df = transformer.fit_transform(self._X_train)

        @resolve_path(lambda: analysis_features_path)
        def _save():
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(feat_df.corr(), ax=ax, cmap="coolwarm", center=0, linewidths=0.3)
            ax.set_title("Feature correlation heatmap (post-engineering)")
            fig.tight_layout()
            fig.savefig("correlation_heatmap.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("analyze_features: saved 1 plot.")

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
            joblib.dump(self._pipeline, "yield_xgboost.joblib")

        _save()

    def evaluate(self):
        y_pred_train = self._pipeline.predict(self._X_train)
        y_pred_test = self._pipeline.predict(self._X_test)

        test_rmse = root_mean_squared_error(self._y_test, y_pred_test)
        target_mean = float(self._y_test.mean())
        target_range = float(self._y_test.max() - self._y_test.min())

        logger.info("--- YieldPredictionXGBoost ---")
        logger.info(f"  RMSE  train={root_mean_squared_error(self._y_train, y_pred_train):.4f}  test={test_rmse:.4f}")
        logger.info(f"  MAE   train={mean_absolute_error(self._y_train, y_pred_train):.4f}  test={mean_absolute_error(self._y_test, y_pred_test):.4f}")
        logger.info(f"  R²    train={r2_score(self._y_train, y_pred_train):.4f}  test={r2_score(self._y_test, y_pred_test):.4f}")
        logger.info(f"  nRMSE (% of mean)  test={test_rmse / target_mean * 100:.1f}%  [target mean={target_mean:.2f}]")
        logger.info(f"  nRMSE (% of range) test={test_rmse / target_range * 100:.1f}%  [target range={target_range:.2f}]")

    def load_pretrained(self, path: Path):
        self._pipeline = joblib.load(path / "yield_xgboost.joblib")

    def _save_feature_importance(self) -> None:
        analysis_features_path = self._analysis_path / "features"
        booster = self._pipeline.named_steps["regressor"]
        importance = pd.Series(
            booster.feature_importances_,
            index=self._pipeline.named_steps["transformer"].get_feature_names_out(),
        ).sort_values()

        @resolve_path(lambda: analysis_features_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 10))
            importance.plot(kind="barh", ax=ax)
            ax.set_title("XGBoost feature importances (tuned model)")
            ax.set_xlabel("Importance")
            ax.axvline(0, color="black", linewidth=0.8)
            fig.tight_layout()
            fig.savefig("feature_importances.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("Feature importance plot saved.")
