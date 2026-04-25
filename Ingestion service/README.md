# HarvestIQ Satellite Ingestion MVP

CLI pipeline for ingesting Sentinel and Landsat data for a given AOI and date range, with deterministic scene selection and reproducible metadata.

## Sources

- `sentinel1` (SAR, Sentinel-1 RTC) - bands: `VV`, `VH`
- `sentinel2` (multispectral, Sentinel-2 L2A) - bands: `B02`, `B03`, `B04`, `B08`, `B11`, `B12`
- `landsat8`, `landsat9` (multispectral, Landsat C2 L2) - bands: `SR_B2`, `SR_B3`, `SR_B4`, `SR_B5`, `SR_B6`, `SR_B7`
- `combined` mode ingests one selected scene per listed source

## Notes

- Provider assets are read remotely and clipped to AOI before local save.
- `--max-cloud` applies to optical sources (`sentinel2`, `landsat8`, `landsat9`) and is ignored for `sentinel1`.
- `--test` downloads one test band per source:
  - `sentinel1`: `VV`
  - `sentinel2`: `B04`
  - `landsat8`: `SR_B4`
  - `landsat9`: `SR_B4`

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
```

```bash
python -m ingestion.ingest --source sentinel2 --aoi-file configs/aoi.geojson --start-date 2025-04-01 --end-date 2025-04-15 --max-cloud 20 --output-dir data/raw
```

```bash
python -m ingestion.ingest --source combined --sources sentinel1,sentinel2,landsat8,landsat9 --aoi-file configs/aoi.geojson --start-date 2024-06-01 --end-date 2024-06-30 --max-cloud 20 --output-dir data/raw --test --verbose
```
