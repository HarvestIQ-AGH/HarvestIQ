import sys
from pathlib import Path

from infrastructure import DataEngine, load_model_class, logger
from infrastructure.local import LocalConfiguration


def _find_latest_version(model_name: str, artifacts_path: Path) -> Path | None:
    model_dir = artifacts_path / model_name
    if not model_dir.exists():
        return None
    versions = [
        d
        for d in model_dir.iterdir()
        if d.is_dir() and d.name.startswith(f"{model_name}_v")
    ]
    if not versions:
        return None
    return max(versions, key=lambda p: int(p.name.split("_v")[1]))


def from_pretrained(model_name: str, config: LocalConfiguration):
    latest = _find_latest_version(model_name, config.paths.artifacts)
    if latest is None:
        logger.error(
            f"No pretrained weights found for '{model_name}' under {config.paths.artifacts}/"
        )
        sys.exit(1)

    logger.info(f"Found pretrained model: {latest}")

    models_root = config.paths.models.resolve()
    model_cls = load_model_class(model_name, models_root)
    model = model_cls(DataEngine(), config)

    logger.info("Cleaning data...")
    model.clean_data()

    logger.info("Loading weights...")
    model.load_pretrained(latest)

    model.interact()
