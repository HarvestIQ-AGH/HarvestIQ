from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests


def stac_search(
    endpoint: str,
    collections: list[str],
    geometry: dict[str, Any] | None,
    bbox: list[float] | None,
    start_date: str,
    end_date: str,
    limit: int = 25,
    query: dict[str, Any] | None = None,
    property_filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {
        "collections": collections,
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "limit": limit,
    }
    if geometry:
        payload["intersects"] = geometry
    elif bbox:
        payload["bbox"] = bbox
    merged_query: dict[str, Any] = {}
    if query:
        merged_query.update(query)
    if property_filters:
        for key, value in property_filters.items():
            merged_query[key] = {"eq": value}
    if merged_query:
        payload["query"] = merged_query

    url = endpoint.rstrip("/") + "/search"
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data.get("features", [])


def download_url(url: str, headers: dict[str, str] | None = None, max_bytes: int | None = None) -> bytes:
    normalized_url = normalize_asset_url(url)
    req_headers = headers or {}
    if max_bytes and "Range" not in req_headers:
        req_headers["Range"] = f"bytes=0-{max_bytes - 1}"
    response = requests.get(normalized_url, headers=req_headers, timeout=120)
    response.raise_for_status()
    return response.content


def normalize_asset_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "s3":
        return url
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return f"https://{bucket}.s3.amazonaws.com/{key}"
