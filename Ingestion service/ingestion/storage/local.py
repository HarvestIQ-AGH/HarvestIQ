from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ingestion.models import DownloadedAsset
from ingestion.utils import ensure_dir


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def scene_dir(self, source: str, scene_id: str) -> Path:
        return self.base_dir / source / scene_id

    def metadata_path(self, source: str, scene_id: str) -> Path:
        return self.scene_dir(source, scene_id) / "metadata.json"

    def is_ingested(self, source: str, scene_id: str) -> bool:
        return self.metadata_path(source, scene_id).exists()

    def write_bytes(self, source: str, scene_id: str, filename: str, content: bytes, source_url: str) -> DownloadedAsset:
        directory = self.scene_dir(source, scene_id)
        ensure_dir(directory)
        path = directory / filename
        path.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        return DownloadedAsset(
            asset_key=filename,
            source_url=source_url,
            local_path=str(path),
            size_bytes=len(content),
            sha256=digest,
        )

    def write_metadata(self, source: str, scene_id: str, metadata: dict[str, Any]) -> str:
        ensure_dir(self.scene_dir(source, scene_id))
        path = self.metadata_path(source, scene_id)
        path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return str(path)
