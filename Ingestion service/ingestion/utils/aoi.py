from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SUPPORTED_SOURCES = {"sentinel1", "sentinel2", "landsat8", "landsat9", "combined"}


def parse_bbox(value: str) -> list[float]:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be in format minx,miny,maxx,maxy")
    bbox = [float(p) for p in parts]
    if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        raise ValueError("bbox coordinates must be minx,miny,maxx,maxy")
    return bbox


def polygon_from_bbox(bbox: list[float]) -> dict[str, Any]:
    minx, miny, maxx, maxy = bbox
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [minx, miny],
                [maxx, miny],
                [maxx, maxy],
                [minx, maxy],
                [minx, miny],
            ]
        ],
    }


def load_aoi(aoi_file: str | None, aoi_wkt: str | None, bbox_arg: str | None) -> tuple[dict[str, Any] | None, list[float] | None]:
    if sum(bool(v) for v in [aoi_file, aoi_wkt, bbox_arg]) != 1:
        raise ValueError("Provide exactly one AOI input: --aoi-file OR --aoi-wkt OR --bbox")

    if bbox_arg:
        bbox = parse_bbox(bbox_arg)
        return polygon_from_bbox(bbox), bbox

    if aoi_file:
        path = Path(aoi_file)
        if not path.exists():
            raise ValueError(f"AOI file not found: {aoi_file}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("type") == "Feature":
            geometry = data.get("geometry")
        elif data.get("type") == "FeatureCollection":
            features = data.get("features") or []
            if not features:
                raise ValueError("GeoJSON FeatureCollection has no features")
            geometry = features[0].get("geometry")
        else:
            geometry = data
        bbox = geometry_to_bbox(geometry)
        return geometry, bbox

    assert aoi_wkt is not None
    geometry = parse_wkt_polygon(aoi_wkt)
    return geometry, geometry_to_bbox(geometry)


def parse_wkt_polygon(wkt: str) -> dict[str, Any]:
    pattern = r"^\s*POLYGON\s*\(\((.+)\)\)\s*$"
    match = re.match(pattern, wkt, flags=re.IGNORECASE)
    if not match:
        raise ValueError("Only POLYGON WKT is supported in MVP")
    coords_raw = match.group(1).split(",")
    coords = []
    for part in coords_raw:
        x_y = part.strip().split()
        if len(x_y) != 2:
            raise ValueError("Invalid WKT coordinate")
        coords.append([float(x_y[0]), float(x_y[1])])
    return {"type": "Polygon", "coordinates": [coords]}


def geometry_to_bbox(geometry: dict[str, Any] | None) -> list[float] | None:
    if not geometry:
        return None
    if geometry.get("type") != "Polygon":
        return None
    coords = geometry.get("coordinates", [[]])[0]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    if not xs or not ys:
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def split_sources(source: str, sources_csv: str | None) -> list[str]:
    if source != "combined":
        return [source]
    if not sources_csv:
        return ["sentinel1", "sentinel2", "landsat8", "landsat9"]
    parts = [s.strip().lower() for s in sources_csv.split(",") if s.strip()]
    if not parts:
        raise ValueError("combined source requires non-empty --sources")
    return parts


def validate_sources(source: str, sources: list[str]) -> None:
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported --source '{source}'")
    for src in sources:
        if src not in SUPPORTED_SOURCES - {"combined"}:
            raise ValueError(f"Unsupported source in combined mode: '{src}'")
