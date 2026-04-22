import shutil

from infrastructure import logger
from infrastructure.local import DEFAULT_PATHS


def clean():
    for path in (DEFAULT_PATHS.artifacts,):
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Removed {path}.")
