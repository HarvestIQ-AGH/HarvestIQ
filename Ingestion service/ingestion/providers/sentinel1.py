from __future__ import annotations

from ingestion.providers.stac_base import StacProvider


class Sentinel1Provider(StacProvider):
    source = "sentinel1"
    stac_endpoint = "https://planetarycomputer.microsoft.com/api/stac/v1"
    collection = "sentinel-1-rtc"
    cloud_aware = False
    test_band = "VV"
    required_bands = ["VV", "VH"]
