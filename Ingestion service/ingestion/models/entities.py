from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class QueryParams:
    source: str
    sources: list[str]
    aoi_geojson: dict[str, Any] | None
    bbox: list[float] | None
    start_date: str
    end_date: str
    max_cloud: float | None
    test: bool
    output_dir: str
    force: bool = False
    config_path: str | None = None


@dataclass(slots=True)
class SceneCandidate:
    source: str
    scene_id: str
    acquisition_time: str
    geometry: dict[str, Any] | None
    bbox: list[float] | None
    properties: dict[str, Any]
    assets: dict[str, dict[str, Any]]
    links: list[dict[str, Any]] = field(default_factory=list)
    score: tuple[Any, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class DownloadedAsset:
    asset_key: str
    source_url: str
    local_path: str
    size_bytes: int
    sha256: str


@dataclass(slots=True)
class IngestionMetadata:
    source: str
    scene_id: str
    acquisition_timestamp: str
    ingestion_timestamp: str
    query_parameters: dict[str, Any]
    source_links: list[str]
    selected_assets: list[str]
    assets: list[dict[str, Any]]
    provider_notes: str | None = None

    @staticmethod
    def now_iso() -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
