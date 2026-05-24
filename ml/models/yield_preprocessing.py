from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

_DB_TABLE = "training-1"
_DROP_COLS = ["YEAR", "FIELD_NAME", "ET_Scaled"]

MONTH_TO_GROWTH_STAGE: dict[int, str] = {
    1:  "dormancy",
    2:  "dormancy",
    3:  "stem_elongation",
    4:  "stem_elongation",
    5:  "booting_heading",
    6:  "flowering",
    7:  "grain_filling",
    8:  "ripening",
    9:  "sowing",
    10: "emergence",
    11: "tillering",
    12: "dormancy",
}

# Phenological ordering used for OrdinalEncoder and plot axis ordering
STAGE_ORDER: list[str] = [
    "sowing", "emergence", "tillering", "dormancy",
    "stem_elongation", "booting_heading", "flowering",
    "grain_filling", "ripening",
]


def load_and_clean(data_engine, db_path: Path) -> pd.DataFrame:
    """Load yield DB, deduplicate, drop known-bad columns, convert DATE to growth stage."""
    df = data_engine.get_sqlite_data(db_path, _DB_TABLE)
    df = df.drop_duplicates()
    df = df.drop(columns=_DROP_COLS)
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["growth_stage"] = df["DATE"].dt.month.map(MONTH_TO_GROWTH_STAGE)
    return df.drop(columns=["DATE"])


def make_column_transformer(
    X: pd.DataFrame,
    *,
    scale: bool,
    ordinal_categorical: bool,
) -> ColumnTransformer:
    """
    Build a ColumnTransformer for yield feature sets.

    Args:
        X: training DataFrame (used only to detect numerical columns).
        scale: apply StandardScaler to numerical features (needed for linear models).
        ordinal_categorical: encode growth_stage as ordinal integers (for tree models)
                             instead of one-hot dummies (for linear models).
    """
    numerical_features = X.select_dtypes(include="number").columns.tolist()
    categorical_features = ["growth_stage"]

    num_steps: list = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        num_steps.append(("scaler", StandardScaler()))

    if ordinal_categorical:
        cat_encoder = OrdinalEncoder(
            categories=[STAGE_ORDER],
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )
    else:
        cat_encoder = OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")

    return ColumnTransformer([
        ("numerical", Pipeline(num_steps), numerical_features),
        ("categorical", Pipeline([("encoder", cat_encoder)]), categorical_features),
    ])
