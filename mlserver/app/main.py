from __future__ import annotations

from typing import Annotated, Literal

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.aoi import BoundingBox
from app.model import MODEL_FEATURES, predict_yield


app = FastAPI(
    title="HarvestIQ ML Server",
    version="0.1.0",
    description="Yield prediction API backed by the bundled XGBoost model.",
    docs_url="/swagger",
    redoc_url="/docs",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    openapi_tags=[
        {"name": "health", "description": "Service health checks."},
        {"name": "yield", "description": "Yield prediction endpoints."},
    ],
)


class AoiResponse(BaseModel):
    bbox: list[float] = Field(..., examples=[[19.90, 50.00, 20.10, 50.15]])
    centroid: dict[str, float]


class YieldPredictionResponse(BaseModel):
    aoi: AoiResponse
    prediction: float
    prediction_unit: str = "model_output"
    placeholder_inputs: bool = True
    features: dict[str, float | str]


@app.get("/health", tags=["health"], summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/predict",
    response_model=YieldPredictionResponse,
    tags=["yield"],
    summary="Predict yield over an AOI",
)
def predict(
    bbox: Annotated[
        str,
        Query(
            description="AOI bounding box as min_lon,min_lat,max_lon,max_lat.",
            examples=["19.90,50.00,20.10,50.15"],
        ),
    ],
    ndvi: Annotated[float, Query(alias="NDVI")] = 0.65,
    msi: Annotated[float, Query(alias="MSI")] = 0.82,
    evi: Annotated[float, Query(alias="EVI")] = 0.42,
    vv: Annotated[float, Query(alias="VV")] = -12.4,
    vh: Annotated[float, Query(alias="VH")] = -18.7,
    vh_vv_ratio: Annotated[float, Query(alias="VH_VV_ratio")] = 1.51,
    lai_scaled: Annotated[float, Query(alias="LAI_Scaled")] = 0.58,
    fapar_scaled: Annotated[float, Query(alias="fAPAR_Scaled")] = 0.61,
    temp_c: Annotated[float, Query(alias="Temp_C")] = 21.5,
    precip_mm_7d_sum: Annotated[float, Query(alias="Precip_mm_7D_sum")] = 18.0,
    soil_clay_pct: Annotated[float, Query(alias="Soil_Clay_pct")] = 22.0,
    soil_sand_pct: Annotated[float, Query(alias="Soil_Sand_pct")] = 41.0,
    soil_organic_c: Annotated[float, Query(alias="Soil_Organic_C")] = 1.8,
    soil_ph_real: Annotated[float, Query(alias="Soil_pH_real")] = 6.4,
    growth_stage: Annotated[
        Literal[
            "booting_heading",
            "dormancy",
            "emergence",
            "flowering",
            "grain_filling",
            "ripening",
            "sowing",
            "stem_elongation",
            "tillering",
        ],
        Query(alias="growth_stage"),
    ] = "tillering",
) -> YieldPredictionResponse:
    try:
        parsed_bbox = BoundingBox.from_query(bbox)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    features: dict[str, float | str] = {
        "NDVI": ndvi,
        "MSI": msi,
        "EVI": evi,
        "VV": vv,
        "VH": vh,
        "VH_VV_ratio": vh_vv_ratio,
        "LAI_Scaled": lai_scaled,
        "fAPAR_Scaled": fapar_scaled,
        "Temp_C": temp_c,
        "Precip_mm_7D_sum": precip_mm_7d_sum,
        "Soil_Clay_pct": soil_clay_pct,
        "Soil_Sand_pct": soil_sand_pct,
        "Soil_Organic_C": soil_organic_c,
        "Soil_pH_real": soil_ph_real,
        "growth_stage": growth_stage,
    }

    return YieldPredictionResponse(
        aoi=AoiResponse(bbox=parsed_bbox.as_list, centroid=parsed_bbox.centroid),
        prediction=predict_yield(features),
        features={feature: features[feature] for feature in MODEL_FEATURES},
    )


def run() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
