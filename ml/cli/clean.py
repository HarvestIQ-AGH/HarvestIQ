import shutil
from infrastructure.logger import logger
from utilities.path_resolver import ARTIFACTS_DEFAULT_PATH


def clean():
    for path in (ARTIFACTS_DEFAULT_PATH, ):
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Removed {path}.")
