from __future__ import annotations

from ingestion.providers.stac_base import StacProvider


class Landsat9Provider(StacProvider):
    source = "landsat9"
    stac_endpoint = "https://planetarycomputer.microsoft.com/api/stac/v1"
    collection = "landsat-c2-l2"
    cloud_aware = True
    cloud_property = "eo:cloud_cover"
    # Planetary Computer STAC property for mission platform.
    property_filters = {"platform": "landsat-9"}
    # Improve temporal comparability by preferring nadir-like view and higher sun.
    numeric_low_preferences = {"view:off_nadir": 2.0}
    numeric_high_preferences = {"view:sun_elevation": 0.2}
    selection_metadata_keys = ["view:off_nadir", "view:sun_azimuth", "view:sun_elevation"]
    test_band = "SR_B4"
    required_bands = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
