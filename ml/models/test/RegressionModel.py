import joblib
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
import seaborn as sns
from feature_engine.encoding import RareLabelEncoder
from feature_engine.outliers import Winsorizer
from feature_engine.selection import DropCorrelatedFeatures
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, QuantileRegressor
from sklearn.metrics import (
    d2_pinball_score,
    mean_absolute_error,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

from infrastructure.local.local_config import LocalConfiguration
from infrastructure.logger import logger
from models.model_base import ModelBase
from models.model_lineage import ModelLineage
from models.train_me import train_me
from utilities.path_resolver import resolve_path


@train_me
class RegressionModel(ModelBase):
    def __init__(self, data_engine, config: LocalConfiguration) -> None:
        super().__init__(data_engine, config)
        self.model_lineage = ModelLineage(self, config.paths.artifacts)

    def clean_data(self):
        df = self.data_engine.get_csv_data(self.config.paths.data / "ames.csv")

        df.columns = df.columns.str.replace(".", "", regex=False)
        df = df.drop(["Order", "PID"], axis="columns")
        df = df.loc[~df["Neighborhood"].isin(["GrnHill", "Landmrk"]), :]
        df = df.loc[df["GrLivArea"] <= 4000, :]
        df = self._replace_na(df)
        df = self._num_to_categorical(df)

        y = df.pop("SalePrice")
        y = np.log1p(y)

        self._categorical_features = df.select_dtypes(include="object").columns
        self._numerical_features = df.select_dtypes(exclude="object").columns

        self._X_train_raw, self._X_test_raw, self._y_train, self._y_test = (
            train_test_split(df, y, test_size=0.3, random_state=0)
        )

    def analyze_data(self) -> None:
        raw = pd.concat([self._X_train_raw, self._X_test_raw])
        target = pd.concat([self._y_train, self._y_test])
        analysis_raw_path = self._analysis_path / "raw"

        @resolve_path(lambda: analysis_raw_path)
        def _save():
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.histplot(target, bins=50, kde=True, ax=ax)
            ax.set_title("SalePrice distribution (log1p)")
            ax.set_xlabel("log1p(SalePrice)")
            fig.tight_layout()
            fig.savefig("saleprice_distribution.png", dpi=150)
            plt.close(fig)

            corr_data = raw[self._numerical_features.tolist()].copy()
            corr_data["SalePrice_log1p"] = target.values
            corr = corr_data.corr()
            top_cols = (
                corr["SalePrice_log1p"]
                .abs()
                .sort_values(ascending=False)
                .iloc[1:16]
                .index.tolist()
            )
            sub_corr = corr.loc[top_cols + ["SalePrice_log1p"], top_cols + ["SalePrice_log1p"]]
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(sub_corr, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5, ax=ax)
            ax.set_title("Correlation heatmap — top numerical features vs SalePrice")
            fig.tight_layout()
            fig.savefig("correlation_heatmap.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("analyze_data: saved 2 plots.")

    def analyze_features(self) -> None:
        analysis_features_path = self._analysis_path / "features"
        X_transformed = self._column_transformer.fit_transform(self._X_train_raw, self._y_train)
        numerical_cols = [c for c in X_transformed.columns if not c.startswith("categorical__")][:10]

        @resolve_path(lambda: analysis_features_path)
        def _save():
            fig, ax = plt.subplots(figsize=(14, 5))
            X_transformed[numerical_cols].boxplot(ax=ax, rot=45)
            ax.set_title("Numerical feature distributions after pipeline transform (train set)")
            ax.set_ylabel("Scaled value")
            fig.tight_layout()
            fig.savefig("numerical_feature_distributions.png", dpi=150)
            plt.close(fig)

        _save()
        logger.info("analyze_features: saved 1 plot.")

    def feature_engineeeing(self):
        numerical_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", MinMaxScaler()),
                ("winsorizer", Winsorizer()),
                (
                    "dropper",
                    DropCorrelatedFeatures(
                        variables=None, method="pearson", threshold=0.85
                    ),
                ),
            ]
        )

        categorical_pipeline = Pipeline(
            [
                ("rare_encoder", RareLabelEncoder(tol=0.01, n_categories=0)),
                (
                    "onehot_encoder",
                    OneHotEncoder(
                        drop="first", handle_unknown="ignore", sparse_output=False
                    ),
                ),
            ]
        )

        self._column_transformer = ColumnTransformer(
            [
                ("numerical", numerical_pipeline, self._numerical_features),
                ("categorical", categorical_pipeline, self._categorical_features),
            ]
        )

        self.model_lineage.add_metadata_entries(
            numerical_pipeline=numerical_pipeline.named_steps
        )
        self.model_lineage.export()

    def train(self):
        X_train = self._column_transformer.fit_transform(
            self._X_train_raw, self._y_train
        )

        self._huber_reg = HuberRegressor(max_iter=2000).fit(X_train, self._y_train)
        self._q_low = QuantileRegressor(quantile=0.35, alpha=0.01, solver="highs").fit(
            X_train, self._y_train
        )
        self._q_high = QuantileRegressor(quantile=0.65, alpha=0.01, solver="highs").fit(
            X_train, self._y_train
        )

        @resolve_path(self.model_lineage.path)
        def _save():
            joblib.dump(self._column_transformer, "ames_transformer.joblib")
            joblib.dump(self._huber_reg, "price_estimator.joblib")
            joblib.dump(self._q_low, "low_price_estimator.joblib")
            joblib.dump(self._q_high, "high_price_estimator.joblib")

        _save()

    def load_pretrained(self, path: Path):
        self._column_transformer = joblib.load(path / "ames_transformer.joblib")
        self._huber_reg = joblib.load(path / "price_estimator.joblib")
        self._q_low = joblib.load(path / "low_price_estimator.joblib")
        self._q_high = joblib.load(path / "high_price_estimator.joblib")

    def evaluate(self):
        X_test = self._column_transformer.transform(self._X_test_raw)
        X_train = self._column_transformer.transform(self._X_train_raw)

        y_train = np.array(self._y_train)
        y_test = np.array(self._y_test)

        for name, model, q in [
            ("Huber (center)", self._huber_reg, None),
            ("QuantileRegressor q=0.35 (low)", self._q_low, 0.35),
            ("QuantileRegressor q=0.65 (high)", self._q_high, 0.65),
        ]:
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)

            # Back-transform from log scale for interpretable metrics
            yt_train = np.expm1(y_train)
            yt_test = np.expm1(y_test)
            yp_train = np.expm1(y_pred_train)
            yp_test = np.expm1(y_pred_test)

            logger.info(f"\n--- {name} ---")
            if q is None:
                logger.info(
                    f"  RMSE  train={root_mean_squared_error(yt_train, yp_train):,.0f}  test={root_mean_squared_error(yt_test, yp_test):,.0f}"
                )
                logger.info(
                    f"  MAE   train={mean_absolute_error(yt_train, yp_train):,.0f}  test={mean_absolute_error(yt_test, yp_test):,.0f}"
                )
            else:
                d2_train = d2_pinball_score(yt_train, yp_train, alpha=q)
                d2_test = d2_pinball_score(yt_test, yp_test, alpha=q)
                logger.info(
                    f"  D² pinball (q={q})  train={d2_train:.4f}  test={d2_test:.4f}"
                )

    def _replace_na(self, df):
        def replace_na(df: pd.DataFrame, col: str, value) -> None:
            df.loc[:, col] = df.loc[:, col].fillna(value)

        # Alley : data description says NA means "no alley access"
        replace_na(df, "Alley", value="None")

        # BedroomAbvGr : NA most likely means 0
        replace_na(df, "BedroomAbvGr", value=0)

        # BsmtQual etc : data description says NA for basement features is "no basement"
        replace_na(df, "BsmtQual", value="No")
        replace_na(df, "BsmtCond", value="No")
        replace_na(df, "BsmtExposure", value="No")
        replace_na(df, "BsmtFinType1", value="No")
        replace_na(df, "BsmtFinType2", value="No")
        replace_na(df, "BsmtFullBath", value=0)
        replace_na(df, "BsmtHalfBath", value=0)
        replace_na(df, "BsmtUnfSF", value=0)

        # Condition : NA most likely means Normal
        replace_na(df, "Condition1", value="Norm")
        replace_na(df, "Condition2", value="Norm")

        # External stuff : NA most likely means average
        replace_na(df, "ExterCond", value="TA")
        replace_na(df, "ExterQual", value="TA")

        # Fence : data description says NA means "no fence"
        replace_na(df, "Fence", value="No")

        # Functional : data description says NA means typical
        replace_na(df, "Functional", value="Typ")

        # GarageType etc : data description says NA for garage features is "no garage"
        replace_na(df, "GarageType", value="No")
        replace_na(df, "GarageFinish", value="No")
        replace_na(df, "GarageQual", value="No")
        replace_na(df, "GarageCond", value="No")
        replace_na(df, "GarageArea", value=0)
        replace_na(df, "GarageCars", value=0)

        # HalfBath : NA most likely means no half baths above grade
        replace_na(df, "HalfBath", value=0)

        # HeatingQC : NA most likely means typical
        replace_na(df, "HeatingQC", value="TA")

        # KitchenAbvGr : NA most likely means 0
        replace_na(df, "KitchenAbvGr", value=0)

        # KitchenQual : NA most likely means typical
        replace_na(df, "KitchenQual", value="TA")

        # LotFrontage : NA most likely means no lot frontage
        replace_na(df, "LotFrontage", value=0)

        # LotShape : NA most likely means regular
        replace_na(df, "LotShape", value="Reg")

        # MasVnrType : NA most likely means no veneer
        replace_na(df, "MasVnrType", value="None")
        replace_na(df, "MasVnrArea", value=0)

        # MiscFeature : data description says NA means "no misc feature"
        replace_na(df, "MiscFeature", value="No")
        replace_na(df, "MiscVal", value=0)

        # OpenPorchSF : NA most likely means no open porch
        replace_na(df, "OpenPorchSF", value=0)

        # PavedDrive : NA most likely means not paved
        replace_na(df, "PavedDrive", value="N")

        # PoolQC : data description says NA means "no pool"
        replace_na(df, "PoolQC", value="No")
        replace_na(df, "PoolArea", value=0)

        # SaleCondition : NA most likely means normal sale
        replace_na(df, "SaleCondition", value="Normal")

        # ScreenPorch : NA most likely means no screen porch
        replace_na(df, "ScreenPorch", value=0)

        # TotRmsAbvGrd : NA most likely means 0
        replace_na(df, "TotRmsAbvGrd", value=0)

        # Utilities : NA most likely means all public utilities
        replace_na(df, "Utilities", value="AllPub")

        # WoodDeckSF : NA most likely means no wood deck
        replace_na(df, "WoodDeckSF", value=0)

        # CentralAir : NA most likely means No
        replace_na(df, "CentralAir", value="N")

        # EnclosedPorch : NA most likely means no enclosed porch
        replace_na(df, "EnclosedPorch", value=0)

        # FireplaceQu : data description says NA means "no fireplace"
        replace_na(df, "FireplaceQu", value="No")
        replace_na(df, "Fireplaces", value=0)

        # SaleCondition : NA most likely means normal sale
        replace_na(df, "SaleCondition", value="Normal")

        # Electrical : NA most likely means standard circuit & breakers
        replace_na(df, "Electrical", value="SBrkr")

        return df

    def _num_to_categorical(self, df):
        df = df.replace(
            {
                "MSSubClass": {
                    20: "SC20",
                    30: "SC30",
                    40: "SC40",
                    45: "SC45",
                    50: "SC50",
                    60: "SC60",
                    70: "SC70",
                    75: "SC75",
                    80: "SC80",
                    85: "SC85",
                    90: "SC90",
                    120: "SC120",
                    150: "SC150",
                    160: "SC160",
                    180: "SC180",
                    190: "SC190",
                },
                "MoSold": {
                    1: "Jan",
                    2: "Feb",
                    3: "Mar",
                    4: "Apr",
                    5: "May",
                    6: "Jun",
                    7: "Jul",
                    8: "Aug",
                    9: "Sep",
                    10: "Oct",
                    11: "Nov",
                    12: "Dec",
                },
            }
        )

        df = df.replace(
            {
                "Alley": {"None": 0, "Grvl": 1, "Pave": 2},
                "BsmtCond": {"No": 0, "Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "BsmtExposure": {"No": 0, "Mn": 1, "Av": 2, "Gd": 3},
                "BsmtFinType1": {
                    "No": 0,
                    "Unf": 1,
                    "LwQ": 2,
                    "Rec": 3,
                    "BLQ": 4,
                    "ALQ": 5,
                    "GLQ": 6,
                },
                "BsmtFinType2": {
                    "No": 0,
                    "Unf": 1,
                    "LwQ": 2,
                    "Rec": 3,
                    "BLQ": 4,
                    "ALQ": 5,
                    "GLQ": 6,
                },
                "BsmtQual": {"No": 0, "Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "ExterCond": {"Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "ExterQual": {"Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "FireplaceQu": {"No": 0, "Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "Functional": {
                    "Sal": 1,
                    "Sev": 2,
                    "Maj2": 3,
                    "Maj1": 4,
                    "Mod": 5,
                    "Min2": 6,
                    "Min1": 7,
                    "Typ": 8,
                },
                "GarageCond": {"No": 0, "Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "GarageQual": {"No": 0, "Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "HeatingQC": {"Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "KitchenQual": {"Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5},
                "LandSlope": {"Sev": 1, "Mod": 2, "Gtl": 3},
                "LotShape": {"IR3": 1, "IR2": 2, "IR1": 3, "Reg": 4},
                "PavedDrive": {"N": 0, "P": 1, "Y": 2},
                "PoolQC": {"No": 0, "Fa": 1, "TA": 2, "Gd": 3, "Ex": 4},
                "Street": {"Grvl": 1, "Pave": 2},
                "Utilities": {"ELO": 1, "NoSeWa": 2, "NoSewr": 3, "AllPub": 4},
            }
        )

        for col in df.select_dtypes(include="object").columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass

        return df
