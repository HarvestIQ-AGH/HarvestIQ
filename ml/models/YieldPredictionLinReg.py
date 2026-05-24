from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNetCV
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from infrastructure import logger
from infrastructure.local import LocalConfiguration
from infrastructure.logger import LoggerMixin
from models import ModelBase, ModelLineage
from models.train_me import train_me
from models.yield_preprocessing import STAGE_ORDER, load_and_clean, make_column_transformer
from utilities import resolve_path


@train_me
class YieldPredictionLinReg(ModelBase, LoggerMixin):
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
        X = pd.concat([self._X_train, self._X_test])
        y = pd.concat([self._y_train, self._y_test])
        df = X.copy()
        df["YIELD"] = y
        analysis_raw_path = self._analysis_path / "raw"

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(df["YIELD"], bins=40)
            mean, median = df["YIELD"].mean(), df["YIELD"].median()
            ax.axvline(mean, color="orange", linestyle="dashed", linewidth=2, label=f"Mean: {mean:.2f}")
            ax.axvline(median, color="red", linestyle="dashed", linewidth=2, label=f"Median: {median:.2f}")
            ax.set_title("Yield distribution")
            ax.set_xlabel("YIELD")
            ax.set_ylabel("Count")
            ax.legend()
            fig.tight_layout()
            fig.savefig("yield_distribution.png", dpi=150)
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(12, 5))
            sns.boxplot(data=df, x="growth_stage", y="YIELD", order=STAGE_ORDER, ax=ax)
            ax.set_title("Yield per phenological growth stage")
            ax.set_xlabel("Growth stage")
            ax.set_ylabel("YIELD")
            fig.tight_layout()
            fig.savefig("yield_per_growth_stage.png", dpi=150)
            plt.close(fig)

            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            corr = df[numeric_cols].corr()[["YIELD"]].drop("YIELD").sort_values("YIELD")
            fig, ax = plt.subplots(figsize=(6, 7))
            corr.plot(kind="barh", ax=ax, legend=False)
            ax.set_title("Feature correlation with YIELD")
            ax.set_xlabel("Pearson r")
            ax.axvline(0, color="black", linewidth=0.8)
            fig.tight_layout()
            fig.savefig("feature_yield_correlation.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("analyze_data: saved 3 plots.")

    def feature_engineeeing(self):
        column_transformer = make_column_transformer(
            self._X_train, scale=True, ordinal_categorical=False
        )
        self._pipeline = Pipeline([
            ("transformer", column_transformer),
            ("regressor", ElasticNetCV(
                l1_ratio=[0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 1.0],
                alphas=np.logspace(-5, 1, 60),
                cv=10,
                max_iter=50000,
                n_jobs=-1,
            )),
        ])
        self.model_lineage.add_metadata_entries(
            numerical_features=self._X_train.select_dtypes(include="number").columns.tolist(),
            categorical_features=["growth_stage"],
        )
        self.model_lineage.export()

    def analyze_features(self) -> None:
        analysis_features_path = self._analysis_path / "features"
        transformer = self._pipeline.named_steps["transformer"]
        feat_df = transformer.fit_transform(self._X_train, self._y_train)
        feat_df = feat_df.loc[:, feat_df.std().fillna(0) > 0]

        @resolve_path(lambda: analysis_features_path)
        def _save():
            fig, ax = plt.subplots(figsize=(14, 12))
            sns.heatmap(feat_df.corr(), ax=ax, cmap="coolwarm", center=0, linewidths=0.3)
            ax.set_title("Feature correlation heatmap (post-engineering)")
            fig.tight_layout()
            fig.savefig("correlation_heatmap.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("analyze_features: saved 1 plot.")

    def train(self):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            self._pipeline.fit(self._X_train, self._y_train)

        reg = self._pipeline.named_steps["regressor"]
        l1_ratios = list(reg.l1_ratio)
        l1_idx = min(range(len(l1_ratios)), key=lambda i: abs(l1_ratios[i] - reg.l1_ratio_))
        alpha_idx = np.argmin(np.abs(reg.alphas_[l1_idx] - reg.alpha_))
        cv_rmse = np.sqrt(reg.mse_path_[l1_idx, alpha_idx].mean())

        logger.info(f"Best alpha:    {reg.alpha_:.6f}")
        logger.info(f"Best l1_ratio: {reg.l1_ratio_:.2f}")
        logger.info(f"CV RMSE: {cv_rmse:.4f}")

        @resolve_path(self.model_lineage.path)
        def _save():
            joblib.dump(self._pipeline, "yield_elasticnet.joblib")

        _save()

    def evaluate(self):
        y_pred_train = self._pipeline.predict(self._X_train)
        y_pred_test = self._pipeline.predict(self._X_test)

        test_rmse = root_mean_squared_error(self._y_test, y_pred_test)
        target_mean = float(self._y_test.mean())
        target_range = float(self._y_test.max() - self._y_test.min())

        logger.info("--- YieldPredictionLinReg ---")
        logger.info(f"  RMSE  train={root_mean_squared_error(self._y_train, y_pred_train):.4f}  test={test_rmse:.4f}")
        logger.info(f"  MAE   train={mean_absolute_error(self._y_train, y_pred_train):.4f}  test={mean_absolute_error(self._y_test, y_pred_test):.4f}")
        logger.info(f"  R²    train={r2_score(self._y_train, y_pred_train):.4f}  test={r2_score(self._y_test, y_pred_test):.4f}")
        logger.info(f"  nRMSE (% of mean)  test={test_rmse / target_mean * 100:.1f}%  [target mean={target_mean:.2f}]")
        logger.info(f"  nRMSE (% of range) test={test_rmse / target_range * 100:.1f}%  [target range={target_range:.2f}]")

    def load_pretrained(self, path: Path):
        self._pipeline = joblib.load(path / "yield_elasticnet.joblib")
