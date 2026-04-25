from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ingestion.clients.stac_api import stac_search
from ingestion.utils.raster import read_remote_raster_clipped_to_bbox

try:
    import planetary_computer
except Exception:  # noqa: BLE001
    planetary_computer = None

LOGGER = logging.getLogger("ingestion.satellite_data_client")


class SatelliteDataClient(ABC):
    """Abstraction for provider-specific STAC search + asset retrieval."""

    @abstractmethod
    def search(
        self,
        collection: str,
        bbox: list[float] | None,
        date_range: tuple[str, str],
        cloud_cover: float | None,
        geometry: dict[str, Any] | None = None,
        property_filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def load_bands(
        self,
        item: dict[str, Any],
        bands: list[str],
        bbox: list[float] | None = None,
    ) -> list[tuple[str, str, bytes, bool]]:
        raise NotImplementedError


class StacEndpointDataClient(SatelliteDataClient):
    def __init__(self, source: str, stac_endpoint: str, sign_asset_urls: bool = True) -> None:
        self.source = source
        self.stac_endpoint = stac_endpoint
        self.sign_asset_urls = sign_asset_urls

    def search(
        self,
        collection: str,
        bbox: list[float] | None,
        date_range: tuple[str, str],
        cloud_cover: float | None,
        geometry: dict[str, Any] | None = None,
        property_filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query = {"eo:cloud_cover": {"lte": cloud_cover}} if cloud_cover is not None else None
        LOGGER.debug(
            "[%s] stac search endpoint=%s collection=%s date_range=%s..%s bbox=%s has_geometry=%s cloud_query=%s property_filters=%s",
            self.source,
            self.stac_endpoint,
            collection,
            date_range[0],
            date_range[1],
            bbox,
            geometry is not None,
            query,
            property_filters,
        )
        features = stac_search(
            endpoint=self.stac_endpoint,
            collections=[collection],
            geometry=geometry,
            bbox=bbox,
            start_date=date_range[0],
            end_date=date_range[1],
            query=query,
            property_filters=property_filters,
        )
        LOGGER.debug("[%s] stac search returned %d feature(s)", self.source, len(features))
        return features

    def load_bands(
        self,
        item: dict[str, Any],
        bands: list[str],
        bbox: list[float] | None = None,
    ) -> list[tuple[str, str, bytes, bool]]:
        return _download_item_bands(item, bands, sign_urls=self.sign_asset_urls, bbox=bbox)


def create_satellite_data_client(
    source: str,
    stac_endpoint: str,
    sign_asset_urls: bool = True,
) -> SatelliteDataClient:
    resolved_endpoint = stac_endpoint.strip() if stac_endpoint else ""
    if not resolved_endpoint:
        raise ValueError(f"Provider {source} must define stac_endpoint")
    return StacEndpointDataClient(source, stac_endpoint=resolved_endpoint, sign_asset_urls=sign_asset_urls)


def _download_item_bands(
    item: dict[str, Any],
    bands: list[str],
    sign_urls: bool,
    bbox: list[float] | None = None,
) -> list[tuple[str, str, bytes, bool]]:
    item_id = item.get("id", "unknown-item")
    assets = item.get("assets", {})
    LOGGER.debug(
        "start band download item=%s requested_bands=%s available_assets=%d sign_urls=%s",
        item_id,
        bands,
        len(assets),
        sign_urls,
    )
    out: list[tuple[str, str, bytes, bool]] = []
    for band in bands:
        asset_key = _resolve_asset_key(assets, band)
        if not asset_key:
            LOGGER.warning("item=%s missing requested band=%s", item_id, band)
            continue
        href = assets.get(asset_key, {}).get("href")
        if not href:
            LOGGER.warning("item=%s band=%s resolved_asset=%s has no href", item_id, band, asset_key)
            continue
        effective_href = _sign_url(href) if sign_urls else href
        clipped_content, clipped = read_remote_raster_clipped_to_bbox(effective_href, bbox)
        if clipped_content is None:
            LOGGER.warning(
                "item=%s band=%s asset_key=%s could not be read/clipped remotely; skipping band",
                item_id,
                band,
                asset_key,
            )
            continue
        content = clipped_content
        LOGGER.debug(
            "item=%s band=%s asset_key=%s downloaded_bytes=%d clipped_to_aoi=%s",
            item_id,
            band,
            asset_key,
            len(content),
            clipped,
        )
        out.append((band, effective_href, content, clipped))
    LOGGER.info("item=%s downloaded %d/%d requested band asset(s)", item_id, len(out), len(bands))
    return out


def _resolve_asset_key(assets: dict[str, Any], requested: str) -> str | None:
    if requested in assets:
        return requested
    candidates = [requested.lower(), requested.upper()]
    aliases = {
        "VV": ["vv"],
        "VH": ["vh"],
        "B02": ["blue", "B2", "b02"],
        "B03": ["green", "B3", "b03"],
        "B04": ["red", "B4", "b04"],
        "B08": ["nir", "nir08", "B8", "b08"],
        "B11": ["swir1", "B11", "b11"],
        "B12": ["swir2", "B12", "b12"],
        "SR_B2": ["blue", "B2", "sr_b2"],
        "SR_B3": ["green", "B3", "sr_b3"],
        "SR_B4": ["red", "B4", "sr_b4"],
        "SR_B5": ["nir", "nir08", "B5", "sr_b5"],
        "SR_B6": ["swir1", "B6", "sr_b6"],
        "SR_B7": ["swir2", "B7", "sr_b7"],
    }
    candidates.extend(aliases.get(requested, []))
    for key in candidates:
        if key in assets:
            if key != requested:
                LOGGER.debug("resolved band alias requested=%s -> asset_key=%s", requested, key)
            return key
    return None


def _sign_url(url: str) -> str:
    if planetary_computer is None:
        raise RuntimeError(
            "signed asset URLs require the planetary-computer package. "
            "Install dependency: planetary-computer."
        )
    signed = str(planetary_computer.sign(url))
    LOGGER.debug("signed asset url for download")
    return signed
