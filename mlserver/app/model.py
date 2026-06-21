from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


MODEL_PATH = Path(__file__).resolve().parents[1] / "yield_xgboost.joblib"

MODEL_FEATURES = [
    "NDVI",
    "MSI",
    "EVI",
    "VV",
    "VH",
    "VH_VV_ratio",
    "LAI_Scaled",
    "fAPAR_Scaled",
    "Temp_C",
    "Precip_mm_7D_sum",
    "Soil_Clay_pct",
    "Soil_Sand_pct",
    "Soil_Organic_C",
    "Soil_pH_real",
    "growth_stage",
]


@lru_cache(maxsize=1)
def load_model() -> Any:
    return joblib.load(MODEL_PATH)


def predict_yield(features: dict[str, float | str]) -> float:
    row = pd.DataFrame([{feature: features[feature] for feature in MODEL_FEATURES}])
    prediction = load_model().predict(row)
    return float(prediction[0])

