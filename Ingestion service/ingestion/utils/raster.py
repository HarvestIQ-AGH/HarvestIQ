from __future__ import annotations

import logging

import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import transform_bounds

LOGGER = logging.getLogger("ingestion.raster_clip")


def read_remote_raster_clipped_to_bbox(
    signed_asset_href: str,
    aoi_bbox_wgs84: list[float] | None,
) -> tuple[bytes | None, bool]:
    """Read remote COG and return AOI-bbox-cropped GeoTIFF bytes."""
    if not aoi_bbox_wgs84:
        return None, False
    if len(aoi_bbox_wgs84) != 4:
        LOGGER.warning("invalid AOI bbox; expected 4 values, got %s", aoi_bbox_wgs84)
        return None, False
    try:
        with rasterio.open(signed_asset_href) as src:
            if not src.crs:
                LOGGER.debug("skip remote clip: source raster has no CRS")
                return None, False
            minx, miny, maxx, maxy = aoi_bbox_wgs84
            minx_r, miny_r, maxx_r, maxy_r = transform_bounds(
                "EPSG:4326",
                src.crs,
                minx,
                miny,
                maxx,
                maxy,
                densify_pts=21,
            )
            window = rasterio.windows.from_bounds(minx_r, miny_r, maxx_r, maxy_r, transform=src.transform)
            window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            if window.width <= 0 or window.height <= 0:
                LOGGER.warning("AOI bbox does not intersect raster extent")
                return None, False
            window = window.round_offsets().round_lengths()
            clipped_data = src.read(window=window)
            clipped_transform = src.window_transform(window)
            profile = src.profile.copy()
            profile.update(
                {
                    "height": clipped_data.shape[1],
                    "width": clipped_data.shape[2],
                    "transform": clipped_transform,
                }
            )
            with MemoryFile() as mem_out:
                with mem_out.open(**profile) as dst:
                    dst.write(clipped_data)
                return mem_out.read(), True
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("remote AOI read/clip failed: %s", exc)
        return None, False
