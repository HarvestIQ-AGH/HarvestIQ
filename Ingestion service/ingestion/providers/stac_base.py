from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from shapely.geometry import shape

from ingestion.clients.satellite_data_client import SatelliteDataClient, create_satellite_data_client
from ingestion.models import DownloadedAsset, IngestionMetadata, QueryParams, SceneCandidate
from ingestion.providers.base import Provider
from ingestion.storage import LocalStorage


LOGGER = logging.getLogger("ingestion.providers.stac")


class StacProvider(Provider):
    """Base implementation for STAC-backed providers.

    Concrete providers (Sentinel-1, Sentinel-2, Landsat, etc.) only define
    source-specific constants such as:
    - `collection`: STAC collection identifier,
    - `stac_endpoint`: STAC API base URL,
    - `required_bands`: assets to download for Bronze,
    - cloud settings (`cloud_aware`, `cloud_property`).

    This class handles the common flow:
    search -> deterministic candidate selection -> asset download -> metadata.
    """

    source = "unknown"
    collection = ""
    stac_endpoint = ""
    sign_asset_urls = True
    cloud_property = "eo:cloud_cover"
    cloud_aware = True
    required_bands: list[str] = []
    test_band: str | None = None
    property_filters: dict[str, Any] = {}
    # Optional quality scoring preferences used in deterministic candidate ranking.
    # target: prefer values close to target_value (penalty by absolute delta * weight)
    numeric_target_preferences: dict[str, tuple[float, float]] = {}
    # low: prefer lower values (penalty by value * weight)
    numeric_low_preferences: dict[str, float] = {}
    # high: prefer higher values (bonus by value * weight)
    numeric_high_preferences: dict[str, float] = {}
    # categorical: bonus when property exactly matches expected value
    categorical_preferences: dict[str, tuple[str, float]] = {}
    # Extra candidate properties persisted to metadata for provenance/debugging.
    selection_metadata_keys: list[str] = []

    def __init__(self) -> None:
        """Create a STAC data client configured by provider constants."""
        self.data_client: SatelliteDataClient = create_satellite_data_client(
            source=self.source,
            stac_endpoint=self.stac_endpoint,
            sign_asset_urls=self.sign_asset_urls,
        )

    def _item_to_candidate(self, item: dict[str, Any]) -> SceneCandidate:
        """Normalize raw STAC feature dict into internal SceneCandidate model."""
        properties = item.get("properties", {})
        return SceneCandidate(
            source=self.source,
            scene_id=item.get("id", "unknown-scene"),
            acquisition_time=properties.get("datetime") or properties.get("start_datetime") or "",
            geometry=item.get("geometry"),
            bbox=item.get("bbox"),
            properties=properties,
            assets=item.get("assets", {}),
            links=item.get("links", []),
        )

    def search(self, query: QueryParams) -> list[SceneCandidate]:
        """Search provider collection and return normalized candidate scenes."""
        cloud_cover = query.max_cloud if self.cloud_aware else None
        LOGGER.info(
            "[%s] searching STAC collection=%s endpoint=%s date=%s..%s",
            self.source,
            self.collection,
            self.stac_endpoint,
            query.start_date,
            query.end_date,
        )
        LOGGER.debug(
            "[%s] search filters bbox=%s has_geometry=%s cloud_cover=%s",
            self.source,
            query.bbox,
            query.aoi_geojson is not None,
            cloud_cover,
        )
        features = self.data_client.search(
            collection=self.collection,
            bbox=query.bbox,
            date_range=(query.start_date, query.end_date),
            cloud_cover=cloud_cover,
            geometry=query.aoi_geojson,
            property_filters=self.property_filters or None,
        )
        LOGGER.info("[%s] STAC search returned %d feature(s)", self.source, len(features))
        return [self._item_to_candidate(f) for f in features]

    def _candidate_cloud(self, candidate: SceneCandidate) -> float:
        """Extract cloud metric used for sorting.

        Uses provider-defined `cloud_property` first and Sentinel-2 specific
        fallback (`s2:cloud_cover`) for compatibility with varying catalogs.
        Missing/invalid values are treated as very cloudy.
        """
        value = candidate.properties.get(self.cloud_property)
        if value is None:
            value = candidate.properties.get("s2:cloud_cover")
        try:
            return float(value)
        except (TypeError, ValueError):
            return 1000.0

    def _bbox_overlap_ratio(self, candidate_bbox: list[float] | None, query_bbox: list[float] | None) -> float:
        """Return intersection(query,candidate)/area(query) for AOI ranking."""
        if not candidate_bbox or not query_bbox:
            return 0.0
        c_minx, c_miny, c_maxx, c_maxy = candidate_bbox
        q_minx, q_miny, q_maxx, q_maxy = query_bbox
        inter_minx = max(c_minx, q_minx)
        inter_miny = max(c_miny, q_miny)
        inter_maxx = min(c_maxx, q_maxx)
        inter_maxy = min(c_maxy, q_maxy)
        if inter_minx >= inter_maxx or inter_miny >= inter_maxy:
            return 0.0
        inter_area = (inter_maxx - inter_minx) * (inter_maxy - inter_miny)
        q_area = (q_maxx - q_minx) * (q_maxy - q_miny)
        if q_area <= 0:
            return 0.0
        return inter_area / q_area

    def _geometry_overlap_ratio(self, candidate: SceneCandidate, query: QueryParams) -> float:
        """Return intersection(query,candidate)/area(query) using exact geometries."""
        if not candidate.geometry or not query.aoi_geojson:
            return self._bbox_overlap_ratio(candidate.bbox, query.bbox)
        try:
            candidate_geom = shape(candidate.geometry)
            query_geom = shape(query.aoi_geojson)
            if query_geom.is_empty or query_geom.area <= 0:
                return 0.0
            return candidate_geom.intersection(query_geom).area / query_geom.area
        except Exception:  # noqa: BLE001
            return self._bbox_overlap_ratio(candidate.bbox, query.bbox)

    def _candidate_number(self, candidate: SceneCandidate, key: str) -> float | None:
        """Safely parse candidate numeric property."""
        value = candidate.properties.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _quality_score(self, candidate: SceneCandidate) -> float:
        """Compute optional provider-specific quality score.

        Higher score means better geometric/illumination consistency.
        """
        score = 0.0
        for key, (target_value, weight) in self.numeric_target_preferences.items():
            value = self._candidate_number(candidate, key)
            if value is None:
                continue
            score -= abs(value - target_value) * weight
        for key, weight in self.numeric_low_preferences.items():
            value = self._candidate_number(candidate, key)
            if value is None:
                continue
            score -= value * weight
        for key, weight in self.numeric_high_preferences.items():
            value = self._candidate_number(candidate, key)
            if value is None:
                continue
            score += value * weight
        for key, (expected, weight) in self.categorical_preferences.items():
            if str(candidate.properties.get(key, "")).lower() == str(expected).lower():
                score += weight
        return score

    def _selection_property_snapshot(self, candidate: SceneCandidate) -> dict[str, Any]:
        """Capture properties used for ranking/provenance."""
        keys = set(self.selection_metadata_keys)
        keys.update(self.numeric_target_preferences.keys())
        keys.update(self.numeric_low_preferences.keys())
        keys.update(self.numeric_high_preferences.keys())
        keys.update(self.categorical_preferences.keys())
        return {k: candidate.properties.get(k) for k in sorted(keys)}

    def select_candidate(self, candidates: list[SceneCandidate], query: QueryParams) -> SceneCandidate | None:
        """Select one deterministic best scene for ingestion.

        Optical sources prioritize AOI overlap, then cloud cover, then newest
        acquisition time. Non-cloud-aware sources skip cloud sorting.
        """
        if not candidates:
            LOGGER.info("[%s] no candidates available for selection", self.source)
            return None
        if self.cloud_aware:
            candidates.sort(
                key=lambda c: (
                    -self._geometry_overlap_ratio(c, query),
                    self._candidate_cloud(c),
                    -self._quality_score(c),
                    -(self._time_to_sort(c.acquisition_time)),
                    c.scene_id,
                )
            )
        else:
            candidates.sort(
                key=lambda c: (
                    -self._geometry_overlap_ratio(c, query),
                    -self._quality_score(c),
                    -(self._time_to_sort(c.acquisition_time)),
                    c.scene_id,
                )
            )
        top = candidates[0]
        quality_score = self._quality_score(top)
        if self.cloud_aware:
            top.score = (
                self._geometry_overlap_ratio(top, query),
                -self._candidate_cloud(top),
                quality_score,
                self._time_to_sort(top.acquisition_time),
            )
        else:
            top.score = (
                self._geometry_overlap_ratio(top, query),
                quality_score,
                self._time_to_sort(top.acquisition_time),
            )
        overlap_ratio = self._geometry_overlap_ratio(top, query)
        overlap_pct = overlap_ratio * 100.0
        LOGGER.info("[%s] selected candidate scene_id=%s", self.source, top.scene_id)
        if overlap_ratio < 0.999:
            full_cover_alternatives: list[SceneCandidate] = []
            partial_alternatives: list[tuple[SceneCandidate, float]] = []
            for candidate in candidates[1:]:
                alt_overlap = self._geometry_overlap_ratio(candidate, query)
                if alt_overlap >= 0.999:
                    full_cover_alternatives.append(candidate)
                else:
                    partial_alternatives.append((candidate, alt_overlap))
            LOGGER.warning(
                "[%s] selected scene does not fully cover AOI: scene_id=%s coverage=%.2f%% (missing %.2f%%)",
                self.source,
                top.scene_id,
                overlap_pct,
                max(0.0, 100.0 - overlap_pct),
            )
            if full_cover_alternatives:
                options = ", ".join(
                    [
                        f"{c.scene_id} (coverage=100.00%, cloud={self._candidate_cloud(c):.2f}, time={c.acquisition_time})"
                        for c in full_cover_alternatives[:3]
                    ]
                )
                LOGGER.warning("[%s] alternative full-coverage scene(s) available: %s", self.source, options)
            elif partial_alternatives:
                partial_alternatives.sort(key=lambda t: t[1], reverse=True)
                options = ", ".join(
                    [
                        f"{c.scene_id} (coverage={ov * 100.0:.2f}%, cloud={self._candidate_cloud(c):.2f}, time={c.acquisition_time})"
                        for c, ov in partial_alternatives[:3]
                    ]
                )
                LOGGER.warning(
                    "[%s] no full-coverage alternative scenes found; best available alternatives: %s",
                    self.source,
                    options,
                )
            else:
                LOGGER.warning(
                    "[%s] no alternative scenes available in current search results (candidate_count=%d). "
                    "Try widening date range or relaxing cloud filter.",
                    self.source,
                    len(candidates),
                )
        else:
            LOGGER.info(
                "[%s] selected scene fully covers AOI: scene_id=%s coverage=%.2f%%",
                self.source,
                top.scene_id,
                overlap_pct,
            )
        LOGGER.debug(
            "[%s] top candidate details acquisition_time=%s cloud=%s overlap=%.4f quality_score=%.3f",
            self.source,
            top.acquisition_time,
            self._candidate_cloud(top),
            overlap_ratio,
            quality_score,
        )
        return top

    def _time_to_sort(self, iso_ts: str) -> int:
        """Convert ISO timestamp to sortable epoch seconds."""
        normalized = iso_ts.replace("Z", "+00:00")
        try:
            return int(__import__("datetime").datetime.fromisoformat(normalized).timestamp())
        except ValueError:
            return 0

    def download(self, candidate: SceneCandidate, query: QueryParams) -> list[DownloadedAsset]:
        """Download required bands for selected scene into local Bronze storage."""
        storage = LocalStorage(query.output_dir)
        downloaded: list[DownloadedAsset] = []
        bands_to_download = [self.test_band] if query.test and self.test_band else self.required_bands
        if query.test and not self.test_band:
            bands_to_download = self.required_bands[:1]
            LOGGER.warning(
                "[%s] --test was enabled but test_band is unset; using first required band=%s",
                self.source,
                bands_to_download[0] if bands_to_download else None,
            )
        LOGGER.info(
            "[%s] downloading %d required band(s) for scene=%s",
            self.source,
            len(bands_to_download),
            candidate.scene_id,
        )
        LOGGER.debug("[%s] bands to download=%s (test=%s)", self.source, bands_to_download, query.test)

        try:
            loaded_bands = self.data_client.load_bands(
                item={
                    "id": candidate.scene_id,
                    "assets": candidate.assets,
                },
                bands=bands_to_download,
                bbox=query.bbox,
            )
            LOGGER.info(
                "[%s] downloaded %d/%d band payload(s) from remote",
                self.source,
                len(loaded_bands),
                len(bands_to_download),
            )
            for band_key, href, content, clipped in loaded_bands:
                filename = self._filename_for_asset(candidate.scene_id, band_key, href)
                downloaded.append(
                    storage.write_bytes(
                        source=self.source,
                        scene_id=candidate.scene_id,
                        filename=filename,
                        content=content,
                        source_url=href,
                    )
                )
                LOGGER.debug(
                    "[%s] wrote asset band=%s file=%s bytes=%d clipped_to_aoi=%s",
                    self.source,
                    band_key,
                    filename,
                    len(content),
                    clipped,
                )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("[%s] failed to load required bands %s: %s", self.source, self.required_bands, exc)
        return downloaded

    def _filename_for_asset(self, scene_id: str, key: str, href: str) -> str:
        """Build deterministic, filesystem-safe local asset filename."""
        parsed_path = urlparse(href).path
        suffix = Path(parsed_path).suffix or ".bin"
        safe_scene = scene_id.replace("/", "_")
        safe_key = key.replace(":", "_")
        return f"{safe_scene}_{safe_key}{suffix}"

    def build_metadata(
        self,
        candidate: SceneCandidate,
        query: QueryParams,
        downloaded: list[DownloadedAsset],
        provider_notes: str | None = None,
    ) -> IngestionMetadata:
        """Create metadata payload saved next to downloaded Bronze assets."""
        platform = candidate.properties.get("platform")
        platform_note = f"Selected platform: {platform}" if platform else None
        merged_notes = " | ".join([note for note in [provider_notes, platform_note] if note]) or None
        selection_properties = self._selection_property_snapshot(candidate)
        return IngestionMetadata(
            source=self.source,
            scene_id=candidate.scene_id,
            acquisition_timestamp=candidate.acquisition_time,
            ingestion_timestamp=IngestionMetadata.now_iso(),
            query_parameters={
                "source": query.source,
                "sources": query.sources,
                "start_date": query.start_date,
                "end_date": query.end_date,
                "max_cloud": query.max_cloud,
                "test": query.test,
                "stac_endpoint": self.stac_endpoint,
                "aoi_bbox": query.bbox,
                "selection_score": candidate.score,
                "selection_properties": selection_properties,
            },
            source_links=self._source_links(candidate),
            selected_assets=self._asset_names(downloaded),
            assets=[
                {
                    "asset_key": a.asset_key,
                    "source_url": a.source_url,
                    "local_path": a.local_path,
                    "size_bytes": a.size_bytes,
                    "sha256": a.sha256,
                }
                for a in downloaded
            ],
            provider_notes=merged_notes,
        )
