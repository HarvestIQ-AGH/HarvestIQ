import shutil

from infrastructure.local.local_config import DEFAULT_PATHS
from infrastructure.logger import logger


def clean():
    for path in (DEFAULT_PATHS.artifacts,):
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Removed {path}.")
