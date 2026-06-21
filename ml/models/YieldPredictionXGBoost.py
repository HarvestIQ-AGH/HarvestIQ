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
from models.yield_preprocessing import STAGE_ORDER, load_and_clean, make_column_transformer
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
        X = pd.concat([self._X_train, self._X_test])
        y = pd.concat([self._y_train, self._y_test])
        df = X.assign(YIELD=y)

        self._save_stage_counts(df)
        self._save_yield_by_stage(df)
        self._save_yield_distribution(df)
        self._save_feature_distributions(df)
        self._save_dynamic_features_by_stage(df)
        self._save_raw_correlation(df)
        logger.info("analyze_data: saved 6 plots.")

    def _save_stage_counts(self, df: pd.DataFrame) -> None:
        analysis_raw_path = self._analysis_path / "raw"
        counts = df["growth_stage"].value_counts().reindex(STAGE_ORDER).dropna()

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, ax = plt.subplots(figsize=(10, 5))
            counts.plot(kind="bar", ax=ax, color="steelblue", edgecolor="black", linewidth=0.5)
            ax.set_title("Sample count per growth stage")
            ax.set_xlabel("Growth stage")
            ax.set_ylabel("Count")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            fig.savefig("stage_counts.png", dpi=150)
            plt.close(fig)

        _save()

    def _save_yield_by_stage(self, df: pd.DataFrame) -> None:
        analysis_raw_path = self._analysis_path / "raw"
        stage_order = [s for s in STAGE_ORDER if s in df["growth_stage"].unique()]

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.boxplot(data=df, x="growth_stage", y="YIELD", order=stage_order, ax=ax, palette="tab10")
            ax.set_title("Yield distribution by growth stage")
            ax.set_xlabel("Growth stage")
            ax.set_ylabel("Yield")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            fig.savefig("yield_by_stage.png", dpi=150)
            plt.close(fig)

        _save()

    def _save_yield_distribution(self, df: pd.DataFrame) -> None:
        analysis_raw_path = self._analysis_path / "raw"

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.histplot(df["YIELD"], kde=True, bins=40, ax=ax, color="steelblue")
            ax.axvline(df["YIELD"].mean(), color="red", linewidth=1, linestyle="--",
                       label=f"mean={df['YIELD'].mean():.2f}")
            ax.axvline(df["YIELD"].median(), color="orange", linewidth=1, linestyle="--",
                       label=f"median={df['YIELD'].median():.2f}")
            ax.set_title("Yield distribution")
            ax.set_xlabel("Yield")
            ax.set_ylabel("Count")
            ax.legend()
            fig.tight_layout()
            fig.savefig("yield_distribution.png", dpi=150)
            plt.close(fig)

        _save()

    def _save_feature_distributions(self, df: pd.DataFrame) -> None:
        analysis_raw_path = self._analysis_path / "raw"
        num_cols = df.select_dtypes(include="number").columns.drop("YIELD").tolist()
        ncols = 4
        nrows = -(-len(num_cols) // ncols)

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, axes = plt.subplots(nrows, ncols, figsize=(16, nrows * 3.5))
            axes_flat = axes.flatten()
            for i, col in enumerate(num_cols):
                sns.histplot(df[col], kde=True, bins=35, ax=axes_flat[i], color="steelblue")
                axes_flat[i].set_title(col, fontsize=9)
                axes_flat[i].set_xlabel("")
            for ax in axes_flat[len(num_cols):]:
                ax.set_visible(False)
            fig.suptitle("Numerical feature distributions", y=1.01)
            fig.tight_layout()
            fig.savefig("feature_distributions.png", dpi=150)
            plt.close(fig)

        _save()

    def _save_dynamic_features_by_stage(self, df: pd.DataFrame) -> None:
        analysis_raw_path = self._analysis_path / "raw"
        dynamic_cols = ["NDVI", "EVI", "LAI_Scaled", "fAPAR_Scaled", "VV", "VH", "Temp_C", "Precip_mm_7D_sum", "MSI", "VH_VV_ratio"]
        stage_order = [s for s in STAGE_ORDER if s in df["growth_stage"].unique()]
        ncols = 2
        nrows = -(-len(dynamic_cols) // ncols)

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, axes = plt.subplots(nrows, ncols, figsize=(16, nrows * 3.5))
            axes_flat = axes.flatten()
            for i, col in enumerate(dynamic_cols):
                sns.boxplot(data=df, x="growth_stage", y=col, order=stage_order,
                            ax=axes_flat[i], palette="tab10")
                axes_flat[i].set_title(col, fontsize=9)
                axes_flat[i].set_xlabel("")
                axes_flat[i].tick_params(axis="x", rotation=45, labelsize=7)
            for ax in axes_flat[len(dynamic_cols):]:
                ax.set_visible(False)
            fig.suptitle("Dynamic features by growth stage", y=1.01)
            fig.tight_layout()
            fig.savefig("dynamic_features_by_stage.png", dpi=150)
            plt.close(fig)

        _save()

    def _save_raw_correlation(self, df: pd.DataFrame) -> None:
        analysis_raw_path = self._analysis_path / "raw"
        num_df = df.select_dtypes(include="number")

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(num_df.corr(), ax=ax, cmap="coolwarm", center=0,
                        linewidths=0.3, annot=True, fmt=".2f", annot_kws={"size": 7})
            ax.set_title("Raw feature correlation (including YIELD)")
            fig.tight_layout()
            fig.savefig("raw_correlation.png", dpi=150)
            plt.close(fig)

        _save()

    def feature_engineeeing(self):
        column_transformer = make_column_transformer(
            self._X_train, scale=False, ordinal_categorical=False
        )
        self._pipeline = Pipeline([
            ("transformer", column_transformer),
            ("regressor", XGBRegressor(random_state=42, n_jobs=-1)),
        ])
        self.model_lineage.add_metadata_entries(
            numerical_features=self._X_train.select_dtypes(include="number").columns.tolist(),
            categorical_features=["growth_stage"],
            categorical_encoding="one_hot",
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

        logger.info(f"--- {type(self).__name__} ---")
        logger.info(f"  RMSE  train={root_mean_squared_error(self._y_train, y_pred_train):.4f}  test={test_rmse:.4f}")
        logger.info(f"  MAE   train={mean_absolute_error(self._y_train, y_pred_train):.4f}  test={mean_absolute_error(self._y_test, y_pred_test):.4f}")
        logger.info(f"  R²    train={r2_score(self._y_train, y_pred_train):.4f}  test={r2_score(self._y_test, y_pred_test):.4f}")
        logger.info(f"  nRMSE (% of mean)  test={test_rmse / target_mean * 100:.1f}%  [target mean={target_mean:.2f}]")
        logger.info(f"  nRMSE (% of range) test={test_rmse / target_range * 100:.1f}%  [target range={target_range:.2f}]")

        eval_df = pd.DataFrame({
            "growth_stage": self._X_test["growth_stage"].values,
            "actual":       self._y_test.values,
            "predicted":    y_pred_test,
            "residual":     y_pred_test - self._y_test.values,
        })

        self._save_rmse_by_growth_stage(eval_df)
        self._save_predicted_vs_actual(eval_df)
        self._save_residuals_by_growth_stage(eval_df)
        self._save_residuals_vs_predicted(eval_df)
        self._save_residuals_distribution(eval_df)

    def load_pretrained(self, path: Path):
        self._pipeline = joblib.load(path / "yield_xgboost.joblib")

    def _save_rmse_by_growth_stage(self, eval_df: pd.DataFrame) -> None:
        analysis_eval_path = self._analysis_path / "evaluation"

        rmse_by_stage = (
            eval_df.groupby("growth_stage")
            .apply(lambda g: root_mean_squared_error(g["actual"], g["predicted"]), include_groups=False)
            .rename("RMSE")
            .sort_index()
        )

        @resolve_path(lambda: analysis_eval_path)
        def _save():
            fig, ax = plt.subplots(figsize=(10, 5))
            rmse_by_stage.plot(kind="bar", ax=ax, color="steelblue", edgecolor="black", linewidth=0.5)
            ax.set_title("Test RMSE by growth stage")
            ax.set_xlabel("Growth stage")
            ax.set_ylabel("RMSE")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            fig.savefig("rmse_by_growth_stage.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info(f"RMSE by growth stage:\n{rmse_by_stage.to_string()}")

    def _save_predicted_vs_actual(self, eval_df: pd.DataFrame) -> None:
        analysis_eval_path = self._analysis_path / "evaluation"

        @resolve_path(lambda: analysis_eval_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 8))
            stages = eval_df["growth_stage"].unique()
            palette = dict(zip(stages, sns.color_palette("tab10", len(stages))))
            for stage, grp in eval_df.groupby("growth_stage"):
                ax.scatter(grp["actual"], grp["predicted"], label=stage, alpha=0.6, s=20, color=palette[stage])
            lims = [eval_df[["actual", "predicted"]].min().min(), eval_df[["actual", "predicted"]].max().max()]
            ax.plot(lims, lims, "k--", linewidth=1, label="perfect")
            ax.set_xlabel("Actual yield")
            ax.set_ylabel("Predicted yield")
            ax.set_title("Predicted vs actual — test set")
            ax.legend(title="Growth stage", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
            fig.tight_layout()
            fig.savefig("predicted_vs_actual.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("predicted_vs_actual.png saved.")

    def _save_residuals_by_growth_stage(self, eval_df: pd.DataFrame) -> None:
        analysis_eval_path = self._analysis_path / "evaluation"

        stage_order = eval_df.groupby("growth_stage")["residual"].median().sort_values().index.tolist()

        @resolve_path(lambda: analysis_eval_path)
        def _save():
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.boxplot(data=eval_df, x="growth_stage", y="residual", order=stage_order, ax=ax, palette="tab10")
            ax.axhline(0, color="black", linewidth=1, linestyle="--")
            ax.set_title("Residuals by growth stage (predicted − actual)")
            ax.set_xlabel("Growth stage")
            ax.set_ylabel("Residual")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            fig.savefig("residuals_by_growth_stage.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("residuals_by_growth_stage.png saved.")

    def _save_residuals_vs_predicted(self, eval_df: pd.DataFrame) -> None:
        analysis_eval_path = self._analysis_path / "evaluation"

        @resolve_path(lambda: analysis_eval_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 6))
            stages = eval_df["growth_stage"].unique()
            palette = dict(zip(stages, sns.color_palette("tab10", len(stages))))
            for stage, grp in eval_df.groupby("growth_stage"):
                ax.scatter(grp["predicted"], grp["residual"], label=stage, alpha=0.6, s=20, color=palette[stage])
            ax.axhline(0, color="black", linewidth=1, linestyle="--")
            ax.set_xlabel("Predicted yield")
            ax.set_ylabel("Residual (predicted − actual)")
            ax.set_title("Residuals vs predicted — test set")
            ax.legend(title="Growth stage", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
            fig.tight_layout()
            fig.savefig("residuals_vs_predicted.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("residuals_vs_predicted.png saved.")

    def _save_residuals_distribution(self, eval_df: pd.DataFrame) -> None:
        analysis_eval_path = self._analysis_path / "evaluation"

        @resolve_path(lambda: analysis_eval_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.histplot(eval_df["residual"], kde=True, ax=ax, bins=40, color="steelblue")
            ax.axvline(0, color="black", linewidth=1, linestyle="--")
            ax.axvline(eval_df["residual"].mean(), color="red", linewidth=1, linestyle="--", label=f"mean={eval_df['residual'].mean():.3f}")
            ax.set_xlabel("Residual (predicted − actual)")
            ax.set_ylabel("Count")
            ax.set_title("Distribution of residuals — test set")
            ax.legend()
            fig.tight_layout()
            fig.savefig("residuals_distribution.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("residuals_distribution.png saved.")

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
