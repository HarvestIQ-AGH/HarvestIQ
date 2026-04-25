from __future__ import annotations

from ingestion.providers.base import Provider
from ingestion.providers.landsat8 import Landsat8Provider
from ingestion.providers.landsat9 import Landsat9Provider
from ingestion.providers.sentinel1 import Sentinel1Provider
from ingestion.providers.sentinel2 import Sentinel2Provider


def create_provider(source: str) -> Provider:
    providers: dict[str, type[Provider]] = {
        "sentinel1": Sentinel1Provider,
        "sentinel2": Sentinel2Provider,
        "landsat8": Landsat8Provider,
        "landsat9": Landsat9Provider,
    }
    if source not in providers:
        raise ValueError(f"Unknown provider source: {source}")
    return providers[source]()
