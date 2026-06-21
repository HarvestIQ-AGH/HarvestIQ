from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    @classmethod
    def from_query(cls, raw_bbox: str) -> "BoundingBox":
        parts = [part.strip() for part in raw_bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must contain four comma-separated values")

        try:
            min_lon, min_lat, max_lon, max_lat = [float(part) for part in parts]
        except ValueError as exc:
            raise ValueError("bbox values must be valid numbers") from exc

        bbox = cls(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)
        bbox.validate()
        return bbox

    @property
    def as_list(self) -> list[float]:
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    @property
    def centroid(self) -> dict[str, float]:
        return {
            "lon": (self.min_lon + self.max_lon) / 2,
            "lat": (self.min_lat + self.max_lat) / 2,
        }

    def validate(self) -> None:
        if not -180 <= self.min_lon <= 180 or not -180 <= self.max_lon <= 180:
            raise ValueError("bbox longitude values must be between -180 and 180")
        if not -90 <= self.min_lat <= 90 or not -90 <= self.max_lat <= 90:
            raise ValueError("bbox latitude values must be between -90 and 90")
        if self.min_lon >= self.max_lon:
            raise ValueError("bbox min_lon must be less than max_lon")
        if self.min_lat >= self.max_lat:
            raise ValueError("bbox min_lat must be less than max_lat")

