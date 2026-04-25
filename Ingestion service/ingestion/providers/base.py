from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ingestion.models import DownloadedAsset, IngestionMetadata, QueryParams, SceneCandidate


class Provider(ABC):
    source: str

    @abstractmethod
    def search(self, query: QueryParams) -> list[SceneCandidate]:
        raise NotImplementedError

    @abstractmethod
    def select_candidate(self, candidates: list[SceneCandidate], query: QueryParams) -> SceneCandidate | None:
        raise NotImplementedError

    @abstractmethod
    def download(self, candidate: SceneCandidate, query: QueryParams) -> list[DownloadedAsset]:
        raise NotImplementedError

    @abstractmethod
    def build_metadata(
        self,
        candidate: SceneCandidate,
        query: QueryParams,
        downloaded: list[DownloadedAsset],
        provider_notes: str | None = None,
    ) -> IngestionMetadata:
        raise NotImplementedError

    def _source_links(self, candidate: SceneCandidate) -> list[str]:
        links: list[str] = []
        for item in candidate.links:
            href = item.get("href")
            if href:
                links.append(href)
        return list(dict.fromkeys(links))

    def _asset_names(self, downloaded: list[DownloadedAsset]) -> list[str]:
        return [asset.asset_key for asset in downloaded]

    def _metadata_dict(self, metadata: IngestionMetadata) -> dict[str, Any]:
        return {
            "source": metadata.source,
            "scene_id": metadata.scene_id,
            "acquisition_timestamp": metadata.acquisition_timestamp,
            "ingestion_timestamp": metadata.ingestion_timestamp,
            "query_parameters": metadata.query_parameters,
            "source_links": metadata.source_links,
            "selected_assets": metadata.selected_assets,
            "assets": metadata.assets,
            "provider_notes": metadata.provider_notes,
        }
