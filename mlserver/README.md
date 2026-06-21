# HarvestIQ ML Server

FastAPI service for the bundled `yield_xgboost.joblib` model.

## Run locally

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Swagger

Swagger UI is available at `http://127.0.0.1:8000/swagger`.
The OpenAPI schema is available at `http://127.0.0.1:8000/openapi.json`.
ReDoc is available at `http://127.0.0.1:8000/docs`.

## Prediction endpoint

```bash
curl "http://127.0.0.1:8000/predict?bbox=19.90,50.00,20.10,50.15"
```

`bbox` is required and represents the AOI as `min_lon,min_lat,max_lon,max_lat`.
The model feature query parameters currently have placeholder defaults and can
be overridden individually:

- `NDVI`
- `MSI`
- `EVI`
- `VV`
- `VH`
- `VH_VV_ratio`
- `LAI_Scaled`
- `fAPAR_Scaled`
- `Temp_C`
- `Precip_mm_7D_sum`
- `Soil_Clay_pct`
- `Soil_Sand_pct`
- `Soil_Organic_C`
- `Soil_pH_real`
- `growth_stage`

Interactive Swagger docs are available at `http://127.0.0.1:8000/swagger`.
