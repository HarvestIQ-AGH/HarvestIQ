from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from ingestion.models import QueryParams
from ingestion.providers.registry import create_provider
from ingestion.storage import LocalStorage
from ingestion.utils import (
    configure_logging,
    load_aoi,
    load_env_file,
    parse_date,
    split_sources,
    validate_sources,
)


LOGGER = logging.getLogger("ingestion.main")

EXIT_SUCCESS = 0
EXIT_VALIDATION_ERROR = 2
EXIT_RUNTIME_ERROR = 1
EXIT_PARTIAL_SUCCESS = 3
EXIT_NO_SCENES = 4


def print_welcome_banner(query: QueryParams, verbose: bool) -> None:
    args_used: list[tuple[str, Any]] = [
        ("source", query.source),
        ("sources", ",".join(query.sources)),
        ("start_date", query.start_date),
        ("end_date", query.end_date),
        ("max_cloud", query.max_cloud),
        ("test", query.test),
        ("output_dir", query.output_dir),
        ("force", query.force),
        ("verbose", verbose),
        ("aoi_bbox", query.bbox),
    ]
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_column("key", style="cyan")
        table.add_column("value", style="white")
        for key, value in args_used:
            table.add_row(key, str(value))
        Console().print(
            Panel.fit(
                table,
                title="HARVESTIQ ingest",
                subtitle="Run configuration",
                border_style="green",
            )
        )
    except Exception:
        print("=== HARVESTIQ ingest ===")
        for key, value in args_used:
            print(f"{key}: {value}")
        print("========================")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ingestion",
        description=(
            "Run HarvestIQ satellite scene ingestion.\n"
            "CLI options override values loaded from --config."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ingestion --source sentinel2 --aoi-file configs/aoi.geojson "
            "--start-date 2025-04-01 --end-date 2025-04-15 --max-cloud 20\n"
            "  ingestion --source combined --sources sentinel1,sentinel2,landsat8,landsat9 "
            "--aoi-file configs/aoi.geojson --start-date 2025-04-01 --end-date 2025-04-15\n"
            "  ingestion --config configs/ingestion.yaml\n"
            "  python -m ingestion.ingest --help"
        ),
    )

    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to YAML config file",
    )

    parser.add_argument(
        "--source",
        choices=["sentinel1", "sentinel2", "landsat8", "landsat9", "combined"],
        help="Primary source to ingest (default: sentinel2)",
    )
    parser.add_argument(
        "--sources",
        metavar="CSV",
        help="Comma-separated source list used when --source combined",
    )

    parser.add_argument("--aoi-file", metavar="PATH", help="AOI GeoJSON file path")
    parser.add_argument("--aoi-wkt", metavar="WKT", help="AOI polygon in WKT format")
    parser.add_argument("--bbox", metavar="MINX,MINY,MAXX,MAXY", help="AOI bounding box")

    parser.add_argument("--start-date", metavar="YYYY-MM-DD", help="Query start date")
    parser.add_argument("--end-date", metavar="YYYY-MM-DD", help="Query end date")
    parser.add_argument(
        "--max-cloud",
        type=float,
        metavar="PCT",
        help="Max cloud cover percent (optical sources only)",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Download only provider test band(s): one asset per source",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        metavar="PATH",
        help="Directory where downloaded scenes are stored (default: %(default)s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if scene metadata already exists",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        metavar="PATH",
        help="Environment file with credentials/token overrides (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging output",
    )
    return parser.parse_args(argv)


def load_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        raise ValueError(f"Config file does not exist: {path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def merge_config(cli: argparse.Namespace, cfg: dict[str, Any]) -> dict[str, Any]:
    merged = dict(cfg)
    cli_dict = vars(cli)
    for key, value in cli_dict.items():
        if value is None:
            continue
        if key in {"force", "verbose"} and value is False:
            continue
        merged[key.replace("-", "_")] = value
    return merged


def build_query(merged: dict[str, Any]) -> QueryParams:
    source = str(merged.get("source", "sentinel2")).lower()
    sources = split_sources(source, merged.get("sources"))
    validate_sources(source, sources)

    if not merged.get("start_date") or not merged.get("end_date"):
        raise ValueError("start_date and end_date are required")
    start_date = parse_date(str(merged["start_date"]))
    end_date = parse_date(str(merged["end_date"]))

    aoi_geojson, bbox = load_aoi(
        merged.get("aoi_file"),
        merged.get("aoi_wkt"),
        merged.get("bbox"),
    )

    return QueryParams(
        source=source,
        sources=sources,
        aoi_geojson=aoi_geojson,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud=merged.get("max_cloud"),
        test=bool(merged.get("test", False)),
        output_dir=merged.get("output_dir", "data/raw"),
        force=bool(merged.get("force", False)),
        config_path=merged.get("config"),
    )


def ingest_single_source(query: QueryParams, source: str) -> tuple[bool, str]:
    provider = create_provider(source)
    storage = LocalStorage(query.output_dir)

    candidates = provider.search(query)
    LOGGER.info("[%s] found %d candidate scene(s)", source, len(candidates))
    candidate = provider.select_candidate(candidates, query)
    if not candidate:
        return False, f"[{source}] no scene found for given filters"

    LOGGER.info("[%s] selected scene: %s", source, candidate.scene_id)
    if storage.is_ingested(source, candidate.scene_id) and not query.force:
        return True, f"[{source}] already ingested {candidate.scene_id}, skipping (use --force to re-download)"

    downloaded = provider.download(candidate, query)
    if not downloaded:
        return False, f"[{source}] scene selected but no downloadable assets were accessible"

    metadata = provider.build_metadata(candidate, query, downloaded, provider_notes=None)
    metadata_path = storage.write_metadata(source, candidate.scene_id, asdict(metadata))
    LOGGER.info("[%s] wrote metadata: %s", source, metadata_path)
    return True, f"[{source}] ingested {candidate.scene_id} with {len(downloaded)} asset(s)"


def run(query: QueryParams) -> int:
    LOGGER.info("Ingestion start: %s", json.dumps(asdict(query), default=str))
    results: list[tuple[bool, str]] = []
    for source in query.sources:
        try:
            ok, message = ingest_single_source(query, source)
            LOGGER.info(message)
            results.append((ok, message))
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("[%s] failed: %s", source, exc)
            results.append((False, f"[{source}] failed: {exc}"))

    successes = [r for r in results if r[0]]
    if not successes:
        return EXIT_NO_SCENES
    if len(successes) < len(results):
        return EXIT_PARTIAL_SUCCESS
    return EXIT_SUCCESS


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    configure_logging(args.verbose)
    load_env_file(args.env_file)
    try:
        config = load_config(args.config)
        merged = merge_config(args, config)
        query = build_query(merged)
        print_welcome_banner(query, verbose=args.verbose)
    except ValueError as exc:
        LOGGER.error("Validation error: %s", exc)
        return EXIT_VALIDATION_ERROR
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to initialize ingestion: %s", exc)
        return EXIT_RUNTIME_ERROR

    try:
        return run(query)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Ingestion failed: %s", exc)
        return EXIT_RUNTIME_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
