from __future__ import annotations

from ingestion.providers.stac_base import StacProvider


class Sentinel2Provider(StacProvider):
    source = "sentinel2"
    stac_endpoint = "https://planetarycomputer.microsoft.com/api/stac/v1"
    collection = "sentinel-2-l2a"
    cloud_aware = True
    cloud_property = "eo:cloud_cover"
    # Small tie-breaker for consistent solar geometry across similar candidates.
    numeric_target_preferences = {"s2:mean_solar_azimuth": (180.0, 0.02)}
    selection_metadata_keys = ["s2:mean_solar_azimuth", "sat:relative_orbit", "sat:orbit_state"]
    test_band = "B04"
    required_bands = ["B02", "B03", "B04", "B08", "B11", "B12"]
